





import threading
import sqlite3
import json
from typing import Any

_pool_size = 10
_active_connections = 0
_lock = threading.Lock()
_db_lock = threading.Lock()
_db = sqlite3.connect(':memory:', check_same_thread=False, isolation_level=None)
_db.row_factory = sqlite3.Row
_db.executescript("""
CREATE TABLE orders (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL, items TEXT NOT NULL, total REAL NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE payments (
    id TEXT PRIMARY KEY, order_id TEXT NOT NULL, amount REAL NOT NULL,
    idempotency_key TEXT NOT NULL, status TEXT NOT NULL, refund_reason TEXT,
    FOREIGN KEY(order_id) REFERENCES orders(id)
);
""")
_db.execute('PRAGMA foreign_keys = ON')


class PooledConnection:
    def __init__(self):
        self._released = False

    def execute(self, query: str, params: tuple = ()) -> dict[str, Any]:
        if self._released:
            raise RuntimeError("Connection already released")

        values = tuple(json.dumps(value) if isinstance(value, (list, dict)) else value for value in params)
        with _db_lock:
            cursor = _db.execute(query.replace('%s', '?'), values)
            if cursor.description:
                row = cursor.fetchone()
                return dict(row) if row is not None else {}
            return {'rows_affected': cursor.rowcount}

    def release(self):
        global _active_connections
        if not self._released:
            self._released = True
            with _lock:
                _active_connections -= 1


def get_connection(timeout_ms: int = 5000) -> PooledConnection:





    global _active_connections
    with _lock:
        if _active_connections >= _pool_size:

            raise TimeoutError(
                f"pool_exhausted: {_active_connections}/{_pool_size} connections in use, "
                f"timeout_ms={timeout_ms}"
            )
        _active_connections += 1
    return PooledConnection()


def pool_stats() -> dict[str, int]:
    return {"pool_size": _pool_size, "active": _active_connections, "available": _pool_size - _active_connections}

