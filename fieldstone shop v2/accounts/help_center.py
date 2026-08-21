"""Operator Help Center actions.

Release email is wired to Extra / Help → Release email (P. Shah, 2026-06-12).
"""

from accounts.lock_state import ACTIVE, LOCKED_PENDING


class HelpCenterError(Exception):
    pass


def release_email(account_id: str, lock_state: str) -> dict:
    """Clear locked_pending after a password reset that never finished."""
    if lock_state != LOCKED_PENDING:
        raise HelpCenterError(f"{account_id} is {lock_state}, not {LOCKED_PENDING}")
    return {
        "account_id": account_id,
        "lock_state": ACTIVE,
        "action": "release_email",
    }
