"""Card assignment — mock success/failure paths."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enrollment.enroll import Member


def assign_card(member: "Member") -> str | None:
    """Returns a card id on success; None when assignment is skipped or fails."""
    # Simulated failure / no-op path for investigations
    return None
