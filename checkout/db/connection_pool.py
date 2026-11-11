"""Fixed-size database connection pool.

Tracks up to 10 active connections. Callers release connections when finished.
Acquisition raises TimeoutError when the pool is full.
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
    """Acquire a connection if capacity is available.

    Raises TimeoutError immediately when all connections are in use.
    timeout_ms is included in the error message; this implementation does not wait.
    """
    global _active_connections
    with _lock:
        if _active_connections >= _pool_size:
            # Report pool capacity and the requested timeout to the caller
            raise TimeoutError(
                f"pool_exhausted: {_active_connections}/{_pool_size} connections in use, "
                f"timeout_ms={timeout_ms}"
            )
        _active_connections += 1
    return PooledConnection()


def pool_stats() -> dict[str, int]:
    return {"pool_size": _pool_size, "active": _active_connections, "available": _pool_size - _active_connections}
