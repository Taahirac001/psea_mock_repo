"""Event publisher — sends events to the message queue.

Known issue: when the queue service is overloaded, events go to DLQ.
The DLQ consumer has no automatic retry and requires manual intervention.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_queue_healthy = True  # Simulated state


def publish_event(event_type: str, payload: dict[str, Any]) -> bool:
    """Publish event to the message queue. Returns True on success."""
    if not _queue_healthy:
        logger.error(f"queue_publish_failed: event={event_type} payload={payload}")
        # Event goes to DLQ — no automatic retry
        _send_to_dlq(event_type, payload)
        return False

    logger.info(f"event_published: type={event_type} payload={payload}")
    return True


def _send_to_dlq(event_type: str, payload: dict[str, Any]) -> None:
    """Dead letter queue — events land here but are never automatically retried.

    BUG: No monitoring alarm on DLQ depth.
    No automatic consumer to retry or alert.
    Events rot in DLQ until someone manually checks.
    """
    logger.warning(f"dlq_enqueue: type={event_type} payload={payload}")
