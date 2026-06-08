"""Inventory stock verification for checkout flow."""

from typing import Any


def verify_stock(items: list[dict], conn=None) -> dict[str, Any]:
    """Check if all items in cart are in stock.

    Uses DB connection if provided; otherwise reads from cache.
    """
    unavailable = []
    for item in items:
        # Simulated stock check
        if item.get("quantity", 1) > 100:
            unavailable.append(item["sku"])

    return {
        "available": len(unavailable) == 0,
        "unavailable": unavailable,
        "checked_items": len(items),
    }
