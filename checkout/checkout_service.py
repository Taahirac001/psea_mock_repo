"""Checkout Service — handles cart-to-order conversion.

Known issue: under high concurrency, DB pool exhaustion causes 503s.
The pool has no max_overflow limit and no circuit breaker.
"""

import time
from typing import Any

from db.connection_pool import get_connection
from inventory.stock_check import verify_stock
from payment.charge import initiate_payment


class CheckoutService:
    def __init__(self):
        self.max_retries = 3
        self.retry_delay_ms = 200

    def process_checkout(self, cart: dict, user_id: str) -> dict[str, Any]:
        """Convert cart to order. Acquires DB connection for the full transaction."""
        conn = None
        for attempt in range(self.max_retries):
            try:
                conn = get_connection(timeout_ms=5000)
                break
            except TimeoutError:
                if attempt == self.max_retries - 1:
                    raise Exception(f"checkout_failed: connection_pool_timeout user={user_id}")
                time.sleep(self.retry_delay_ms / 1000)

        try:
            # Hold connection for entire checkout flow (problematic under load)
            stock_result = verify_stock(cart["items"], conn=conn)
            if not stock_result["available"]:
                return {"status": "failed", "reason": "out_of_stock", "items": stock_result["unavailable"]}

            order_id = self._create_order(conn, cart, user_id)
            payment = initiate_payment(conn, order_id, cart["total"])

            if payment["status"] != "success":
                self._rollback_order(conn, order_id)
                return {"status": "failed", "reason": "payment_declined"}

            self._finalize_order(conn, order_id)
            return {"status": "success", "order_id": order_id}
        finally:
            if conn:
                conn.release()  # Connection held for entire flow duration

    def _create_order(self, conn, cart: dict, user_id: str) -> str:
        result = conn.execute(
            "INSERT INTO orders (user_id, items, total, status) VALUES (%s, %s, %s, 'PENDING') RETURNING id",
            (user_id, cart["items"], cart["total"]),
        )
        return result["id"]

    def _finalize_order(self, conn, order_id: str) -> None:
        conn.execute("UPDATE orders SET status = 'CONFIRMED' WHERE id = %s", (order_id,))

    def _rollback_order(self, conn, order_id: str) -> None:
        conn.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = %s", (order_id,))
