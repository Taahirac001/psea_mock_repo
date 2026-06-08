"""Database connection pool — no max_overflow, no circuit breaker.

This is the root cause of checkout 503s under load.
Pool size is fixed at 10 but there's no backpressure mechanism.
When all 10 connections are held by long-running checkout transactions,
new requests block until timeout_ms expires, then raise TimeoutError.
"""

import threading
from typing import Any

_pool_size = 10  # Fixed pool, no overflow allowed
_active_connections = 0
_lock = threading.Lock()


class PooledConnection:
    def __init__(self):
        self._released = False

    def execute(self, query: str, params: tuple = ()) -> dict[str, Any]:
        if self._released:
            raise RuntimeError("Connection already released")
        # Simulated query execution
        return {"id": "ord_mock_001", "rows_affected": 1}

    def release(self):
        global _active_connections
        if not self._released:
            self._released = True
            with _lock:
                _active_connections -= 1


def get_connection(timeout_ms: int = 5000) -> PooledConnection:
    """Acquire a connection from the pool. Blocks until timeout.

    BUG: No max_overflow, no queuing priority, no circuit breaker.
    Under sustained load (>10 concurrent checkouts), all connections
    are held for the full checkout duration (stock check + payment + DB writes).
    New requests queue and timeout after 5s → 503 to the client.
    """
    global _active_connections
    with _lock:
        if _active_connections >= _pool_size:
            # In production this blocks; here we simulate the timeout path
            raise TimeoutError(
                f"pool_exhausted: {_active_connections}/{_pool_size} connections in use, "
                f"timeout_ms={timeout_ms}"
            )
        _active_connections += 1
    return PooledConnection()


def pool_stats() -> dict[str, int]:
    return {"pool_size": _pool_size, "active": _active_connections, "available": _pool_size - _active_connections}
