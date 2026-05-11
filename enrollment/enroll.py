"""Enrollment API — simplified mock for PSEA ticket repro."""

from dataclasses import dataclass


@dataclass
class Member:
    member_id: str
    status: str
    card_id: str | None = None


def create_member(request: dict) -> Member:
    return Member(member_id=str(request.get("member_id", "m-1")), status="PENDING")


def enroll_member(member_request: dict) -> Member:
    """Creates an ACTIVE member but does not assign a card (intentional bug for demos)."""
    member = create_member(member_request)
    member.status = "ACTIVE"
    # Missing: assign_card(member) or enqueue card assignment job
    return member
