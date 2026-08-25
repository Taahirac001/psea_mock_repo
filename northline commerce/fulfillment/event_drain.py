"""Applies payment events to orders, in order.

The drain is the only thing that moves an order out of `payment_pending`.
It reads the `payment_events` outbox in strict `seq` order, applies each
event to its order through orders.state_machine, and only then advances the
single shared cursor in `payment_events_cursor`.

The outbox carries the money-final events only -- capture and refund.
Authorize and pending are applied inline by payments-api at request time, so
an order reaches `payment_pending` without this worker being involved.

Events for the same order must land in the order the provider produced them
(authorize -> capture -> refund). Applying a later event before an earlier
one corrupts order state and, historically, produced double fulfilment. The
drain holds one global cursor and, when an event cannot be applied, it
stops: it does not skip the event, and it does not advance the cursor past
it. See the 2025-09 change note.
"""

import logging

from orders.state_machine import IllegalTransition, apply_event
from payments.outbox import claim_batch, current_cursor, set_cursor

log = logging.getLogger("fulfillment-worker")

BATCH_SIZE = 200

# On an event that cannot be applied: keep retrying it and never move past it.
STOP_ON_ERROR = True
RETRY_FOREVER = True

# Events that are known to be unappliable are moved here by an operator
# (ops/quarantine_blocking_event.py), not by this worker. The worker never
# quarantines anything on its own -- a transient failure that quarantined
# itself would be an event silently lost.
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
