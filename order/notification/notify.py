"""Notification service client — sends user notifications.

Known issue: 30s timeout on the HTTP call to notification-service.
When notification-service is degraded, this blocks the calling thread
for the full 30s before raising TimeoutError. No async/fire-and-forget pattern.
"""

import logging

logger = logging.getLogger(__name__)

NOTIFICATION_TIMEOUT_SECONDS = 30


def send_order_notification(order_id: str, user_id: str, event: str = "confirmed") -> bool:
    """Send notification to user about order event.

    BUG: Synchronous HTTP call with 30s timeout.
    If notification-service is slow/down, this blocks order confirmation flow.
    No circuit breaker, no async dispatch.
    """
    try:
        # Simulated HTTP call to notification-service
        response = _http_post(
            url="http://notification-service:8080/send",
            json={"order_id": order_id, "user_id": user_id, "event": event},
            timeout=NOTIFICATION_TIMEOUT_SECONDS,
        )
        if response.get("status") == "sent":
            logger.info(f"notification_sent: order={order_id} user={user_id} event={event}")
            return True
        logger.warning(f"notification_failed: order={order_id} response={response}")
        return False
    except TimeoutError:
        logger.error(f"notification_timeout: order={order_id} user={user_id} timeout={NOTIFICATION_TIMEOUT_SECONDS}s")
        raise


def _http_post(url: str, json: dict, timeout: int) -> dict:
    """Simulated HTTP client."""
    # In production this calls requests.post or httpx
    raise TimeoutError(f"Connection to {url} timed out after {timeout}s")
