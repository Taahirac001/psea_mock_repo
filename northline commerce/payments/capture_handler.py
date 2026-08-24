"""Records what the payment provider tells us, and nothing else.

This service is deliberately dumb: it verifies the callback signature,
records the payment row, and either applies the pre-capture state inline or
appends an event to the outbox.

  * authorize / pending -- applied inline. Nothing is money-final yet and
    there is no ordering risk, so checkout does not have to wait on a worker.
  * capture / refund -- appended to `payment_events` and applied by the
    fulfilment worker in strict order (fulfillment/event_drain.py). These are
    money-final and must never be applied out of order.

So the only thing that moves an order out of `payment_pending` is the drain.
That split is why a stuck-order incident shows healthy logs here: a capture
recorded on this side proves the money moved, and proves nothing at all about
whether the order advanced.
"""

import logging

from payments.outbox import EVENTS_TABLE

log = logging.getLogger("payments-api")

INLINE_EVENTS = ("payment.authorized", "payment.pending")
OUTBOX_EVENTS = ("payment.captured", "payment.refunded")


def handle_callback(db, callback, request_id: str) -> int:
    """Record the provider callback; queue it if it is money-final."""
    if callback.event_type not in INLINE_EVENTS + OUTBOX_EVENTS:
        log.warning(
            "callback ignored event=%s order=%s request_id=%s",
            callback.event_type,
            callback.order_id,
            request_id,
        )
        return 0

    record_payment(db, callback)

    if callback.event_type in INLINE_EVENTS:
        from orders.state_machine import apply_event

        apply_event(db, callback)
        log.info(
            "callback applied inline event=%s order=%s request_id=%s",
            callback.event_type,
            callback.order_id,
            request_id,
        )
        return 0

    seq = db.scalar(
        f"INSERT INTO {EVENTS_TABLE} (order_id, event_type, payload, created_at) "
        "VALUES (:order_id, :event_type, :payload, now()) RETURNING seq",
        {
            "order_id": callback.order_id,
            "event_type": callback.event_type,
            "payload": callback.payload,
        },
    )
    log.info(
        "callback recorded event=%s order=%s amount_minor=%s seq=%s request_id=%s",
        callback.event_type,
        callback.order_id,
        callback.amount_minor,
        seq,
        request_id,
    )
    return seq


def record_payment(db, callback) -> None:
    """Upsert the payments row. Capture state comes from the provider only."""
    db.execute(
        "INSERT INTO payments (order_id, auth_state, capture_state, amount_minor, "
        "currency, captured_at) VALUES (:order_id, :auth, :capture, :amount, "
        ":currency, :captured_at) ON CONFLICT (order_id) DO UPDATE SET "
        "auth_state = :auth, capture_state = :capture, captured_at = :captured_at",
        {
            "order_id": callback.order_id,
            "auth": callback.auth_state,
            "capture": callback.capture_state,
            "amount": callback.amount_minor,
            "currency": callback.currency,
            "captured_at": callback.captured_at,
        },
    )
