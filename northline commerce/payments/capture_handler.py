"""Records provider payment callbacks; money-final events go to the outbox."""

import logging

from payments.outbox import EVENTS_TABLE

log = logging.getLogger("payments-api")

# Applied inline at request time -- not money-final, no ordering risk.
INLINE_EVENTS = ("payment.authorized", "payment.pending")
# Money-final: appended to payment_events, applied by fulfillment/event_drain.py
# in strict seq order.
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
