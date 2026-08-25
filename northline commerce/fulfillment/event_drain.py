"""Applies payment events to orders in strict `seq` order."""

import logging

from orders.state_machine import IllegalTransition, apply_event
from payments.outbox import claim_batch, current_cursor, set_cursor

log = logging.getLogger("fulfillment-worker")

BATCH_SIZE = 200

# Never skip an unappliable event and never advance past it -- out-of-order
# application has produced double fulfilment before (2025-09 change note).
STOP_ON_ERROR = True
RETRY_FOREVER = True

# Unappliable events are moved here by an operator
# (ops/quarantine_blocking_event.py), never by this worker.
DEAD_LETTER_TABLE = "payment_events_dead_letter"


def drain_once(db) -> int:
    """Apply events from the cursor forward; stop at the first unappliable one."""
    cursor = current_cursor(db)
    applied = 0
    for event in claim_batch(db, after_seq=cursor, limit=BATCH_SIZE):
        try:
            apply_event(db, event)
        except IllegalTransition as exc:
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
    """Events sitting unapplied behind the cursor."""
    return db.scalar(
        "SELECT count(*) FROM payment_events WHERE seq > :c",
        {"c": current_cursor(db)},
    )
