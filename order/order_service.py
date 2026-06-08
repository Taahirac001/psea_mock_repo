"""Order Service — manages order lifecycle and fulfillment.

Known issue: orders can get stuck in PENDING when:
1. The notification service times out during order confirmation
2. The DLQ consumer crashes and stops processing failed events
3. The order state machine doesn't have a timeout/recovery mechanism
"""

import logging
from typing import Any
from datetime import datetime, timezone

from notification.notify import send_order_notification
from queue_service.publisher import publish_event

logger = logging.getLogger(__name__)

ORDER_STATES = ["PENDING", "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]


class OrderService:
    def __init__(self, db_conn):
        self.conn = db_conn

    def confirm_order(self, order_id: str) -> dict[str, Any]:
        """Transition order from PENDING to CONFIRMED and notify."""
        order = self._get_order(order_id)
        if not order:
            return {"status": "error", "reason": "order_not_found"}

        if order["status"] != "PENDING":
            return {"status": "error", "reason": f"invalid_transition: {order['status']} -> CONFIRMED"}

        # Update order status
        self.conn.execute(
            "UPDATE orders SET status = 'CONFIRMED', confirmed_at = %s WHERE id = %s",
            (datetime.now(timezone.utc).isoformat(), order_id),
        )

        # Publish event to queue for downstream processing
        publish_event("order.confirmed", {"order_id": order_id, "user_id": order["user_id"]})

        # Send notification — BUG: if this times out, order stays CONFIRMED
        # but user never gets notified, and fulfillment may not trigger
        try:
            send_order_notification(order_id, order["user_id"], event="confirmed")
        except TimeoutError as e:
            # Swallowed timeout — no retry mechanism, no dead letter
            logger.warning(f"notification_timeout: order={order_id} error={e}")
            # Order is already CONFIRMED in DB but notification failed silently

        return {"status": "success", "order_id": order_id, "new_status": "CONFIRMED"}

    def get_order_status(self, order_id: str) -> dict[str, Any]:
        order = self._get_order(order_id)
        if not order:
            return {"status": "error", "reason": "order_not_found"}
        return {"order_id": order_id, "status": order["status"], "created_at": order["created_at"]}

    def _get_order(self, order_id: str) -> dict[str, Any] | None:
        result = self.conn.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        return result if result and result.get("id") else None
