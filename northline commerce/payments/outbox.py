"""The payment_events outbox and its single cursor.

payments-api appends events here when the provider tells us something
happened. fulfillment-worker reads them in `seq` order and advances the
cursor. There is exactly one cursor for the whole stream -- ordering is
global, not per order, so the cursor cannot advance past an event that
cannot be applied.

Nothing in this module skips an event. Moving an event out of the stream is
an operator action, never an automatic one.
"""

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
