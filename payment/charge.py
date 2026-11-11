






import uuid
from typing import Any


def initiate_payment(conn, order_id: str, amount: float, idempotency_key: str | None = None) -> dict[str, Any]:

    if idempotency_key is None:
        idempotency_key = f"pay_{order_id}_{uuid.uuid4().hex[:8]}"




    existing = conn.execute(
        "SELECT id, status FROM payments WHERE idempotency_key = %s",
        (idempotency_key,),
    )
    if existing and existing.get("id"):
        return {"status": "already_processed", "payment_id": existing["id"]}


    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    conn.execute(
        "INSERT INTO payments (id, order_id, amount, idempotency_key, status) VALUES (%s, %s, %s, %s, 'SUCCESS')",
        (payment_id, order_id, amount, idempotency_key),
    )

    return {"status": "success", "payment_id": payment_id, "amount": amount}


def refund_payment(conn, payment_id: str, reason: str = "") -> dict[str, Any]:

    conn.execute(
        "UPDATE payments SET status = 'REFUNDED', refund_reason = %s WHERE id = %s",
        (reason, payment_id),
    )
    return {"status": "refunded", "payment_id": payment_id}

