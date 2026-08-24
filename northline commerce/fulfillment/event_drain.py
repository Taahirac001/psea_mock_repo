"""Applies payment events to orders, in order.

The drain is the only thing that moves an order out of `payment_pending`.
It reads the `payment_events` outbox in strict `seq` order, applies each
event to its order through orders.state_machine, and only then advances the
single shared cursor in `payment_events_cursor`.

The outbox carries the money-final events only -- capture and refund.
Authorize and pending are applied inline by payments-api at request time, so
an order reaches `payment_pending` without this worker being involved. It
takes the drain to get any further than that.

WHY STRICTLY ORDERED, AND WHY IT STOPS INSTEAD OF SKIPPING
----------------------------------------------------------
Events for the same order must land in the order the provider produced them
(authorize -> capture -> refund). Applying a later event before an earlier
one corrupts order state and, historically, produced double fulfilment. So
the drain holds one global cursor and, when an event cannot be applied, it
STOPS. It does not skip the event, and it does not advance the cursor past
it. See the 2025-09 change note.

The cost of that guarantee: ONE event that can never be applied blocks every
event behind it. The pipeline is still healthy, the worker is still running
and heart-beating, captures are still being recorded by payments-api -- but
no order advances, and the backlog grows for as long as the head event sits
there. On the storefront that looks like "charged but still awaiting
payment", on more and more orders.

If you are here because orders are stuck in `payment_pending`: read the
head-of-line event out of the log (`apply failed seq=<n> order=<id>`) or
with ops/stuck_orders.sql, then follow ops/quarantine_blocking_event.py.
Do NOT change RETRY_FOREVER or STOP_ON_ERROR to clear an incident -- both
exist to keep events from being applied out of order, and turning either off
trades a stuck queue for silently corrupted orders.
"""

import logging

from orders.state_machine import IllegalTransition, apply_event
from payments.outbox import claim_batch, current_cursor, set_cursor

log = logging.getLogger("fulfillment-worker")

BATCH_SIZE = 200

# On an event that cannot be applied: keep retrying it and never move past it.
STOP_ON_ERROR = True
RETRY_FOREVER = True

# Events that are known to be unappliable are moved here by an operator, not
# by this worker. The worker never quarantines anything on its own -- a
# transient failure that quarantined itself would be an event silently lost.
DEAD_LETTER_TABLE = "payment_events_dead_letter"


def drain_once(db) -> int:
    """Apply as many events as possible from the cursor forward.

    Returns the number of events applied. Stops at the first event that
    cannot be applied, leaving the cursor pointing before it.
    """
    cursor = current_cursor(db)
    applied = 0
    for event in claim_batch(db, after_seq=cursor, limit=BATCH_SIZE):
        try:
            apply_event(db, event)
        except IllegalTransition as exc:
            # Head of line. The cursor is NOT advanced: this event and
            # everything behind it stay unapplied until an operator resolves
            # this one event.
            log.error(
                "apply failed seq=%s order=%s event=%s from_state=%s "
                "reason=illegal_transition backlog=%s "
                "(fulfillment/event_drain.py:drain_once)",
                event.seq,
                event.order_id,
                event.event_type,
                exc.from_state,
                backlog_depth(db),
            )
            if STOP_ON_ERROR:
                return applied
        set_cursor(db, event.seq)
        applied += 1
    return applied


def backlog_depth(db) -> int:
    """How many events are sitting unapplied behind the cursor."""
    return db.scalar(
        "SELECT count(*) FROM payment_events WHERE seq > :c",
        {"c": current_cursor(db)},
    )
