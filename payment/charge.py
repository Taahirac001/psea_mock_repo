"""Payment service — processes charges for orders.

Known issue: idempotency key check has a race condition.
Two concurrent requests with the same idempotency_key can both pass
the SELECT check before either INSERT completes, resulting in double charges.
"""

import uuid
from typing import Any


def initiate_payment(conn, order_id: str, amount: float, idempotency_key: str | None = None) -> dict[str, Any]:
    """Charge the customer. Uses idempotency_key to prevent duplicate charges."""
    if idempotency_key is None:
        idempotency_key = f"pay_{order_id}_{uuid.uuid4().hex[:8]}"

    # Check for existing payment with this idempotency key
    # BUG: This is a read-then-write race condition.
    # Two concurrent requests can both see "no existing payment" and both proceed.
    existing = conn.execute(
        "SELECT id, status FROM payments WHERE idempotency_key = %s",
        (idempotency_key,),
    )
    if existing and existing.get("id"):
        return {"status": "already_processed", "payment_id": existing["id"]}

    # Process the charge (no SELECT FOR UPDATE, no advisory lock)
    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO payments (id, order_id, amount, idempotency_key, status) VALUES (%s, %s, %s, %s, 'SUCCESS')",
        (payment_id, order_id, amount, idempotency_key),
    )

    return {"status": "success", "payment_id": payment_id, "amount": amount}


def refund_payment(conn, payment_id: str, reason: str = "") -> dict[str, Any]:
    """Issue a refund for a processed payment."""
    conn.execute(
        "UPDATE payments SET status = 'REFUNDED', refund_reason = %s WHERE id = %s",
        (reason, payment_id),
    )
    return {"status": "refunded", "payment_id": payment_id}
