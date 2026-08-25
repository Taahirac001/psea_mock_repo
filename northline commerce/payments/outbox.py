"""The payment_events outbox and its single global cursor."""

CURSOR_TABLE = "payment_events_cursor"
EVENTS_TABLE = "payment_events"
DEAD_LETTER_TABLE = "payment_events_dead_letter"


def connect(env: str):
    """Connect to the orders database for an environment."""
    from platform_db import connect_for_env

    return connect_for_env(env, role="orders")


def current_cursor(db) -> int:
    return db.scalar(f"SELECT seq FROM {CURSOR_TABLE}")


def set_cursor(db, seq: int) -> None:
    # claim_batch never reads at or below the cursor: moving it past a live
    # event abandons that event with no record. Only
    # ops/quarantine_blocking_event.py does that, and it dead-letters first.
    db.execute(f"UPDATE {CURSOR_TABLE} SET seq = :seq", {"seq": seq})


def claim_batch(db, after_seq: int, limit: int):
    return db.query(
        f"SELECT seq, order_id, event_type, payload, created_at "
        f"FROM {EVENTS_TABLE} WHERE seq > :after ORDER BY seq LIMIT :limit",
        {"after": after_seq, "limit": limit},
    )


def dead_letter(db, seq: int, reason: str) -> None:
    """Move one event out of the stream, keeping the original row and why."""
    db.execute(
        f"INSERT INTO {DEAD_LETTER_TABLE} "
        f"(seq, order_id, event_type, payload, created_at, reason, quarantined_at) "
        f"SELECT seq, order_id, event_type, payload, created_at, :reason, now() "
        f"FROM {EVENTS_TABLE} WHERE seq = :seq",
        {"seq": seq, "reason": reason},
    )
    db.execute(f"DELETE FROM {EVENTS_TABLE} WHERE seq = :seq", {"seq": seq})
