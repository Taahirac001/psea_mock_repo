

from typing import Any


def verify_stock(items: list[dict], conn=None) -> dict[str, Any]:




    unavailable = []
    for item in items:

        if item.get("quantity", 1) > 100:
            unavailable.append(item["sku"])

    return {
        "available": len(unavailable) == 0,
        "unavailable": unavailable,
        "checked_items": len(items),
    }

