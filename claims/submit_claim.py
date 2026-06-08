"""Claims submission — validates and processes insurance/billing claims.

Known issue: When cardId is null (due to enrollment bug in enroll.py),
claims are rejected with a cryptic 'INVALID_BILLING_REF' error.
The error message doesn't indicate the root cause is a missing card assignment.
"""

from typing import Any


def submit_claim(member_id: str, card_id: str | None, claim_amount: float, service_date: str) -> dict[str, Any]:
    """Submit a claim for processing.

    Requires:
        - member_id: active enrolled member
        - card_id: assigned billing card (MUST NOT be None)
        - claim_amount: positive decimal
        - service_date: ISO date string
    """
    # Validation
    if not member_id:
        return {"status": "rejected", "error": "MISSING_MEMBER_ID"}

    if card_id is None or card_id.strip() == "":
        # This is the failure path triggered by the enrollment bug
        # Error message is misleading — doesn't say "card not assigned"
        return {"status": "rejected", "error": "INVALID_BILLING_REF", "detail": "billing reference validation failed"}

    if claim_amount <= 0:
        return {"status": "rejected", "error": "INVALID_AMOUNT"}

    # Process claim
    return {
        "status": "accepted",
        "claim_id": f"CLM-{member_id}-{service_date}",
        "member_id": member_id,
        "card_id": card_id,
        "amount": claim_amount,
    }
