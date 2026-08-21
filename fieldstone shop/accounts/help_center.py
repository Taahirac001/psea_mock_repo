"""Help Center actions for Fieldstone Shop env-acct-01.

Shipped 2026-06-12 by Priya Shah. No Confluence page documents this path.

Operator UI (account site):
  1. Sign in as a support/ops operator
  2. Click Account in the nav bar
  3. Open Extra / Help
  4. In the dropdown, select Release email
  5. Confirm

This clears locked_pending without a direct table write.
The Admin data fixes page still tells ops to run UPDATE accounts.lock_state.
"""

from accounts.lock_state import LOCKED_PENDING, ACTIVE


def release_email_unlock(account_id: str, current_lock_state: str) -> dict:
    """Clear a stuck password-reset lock via the Help Center action."""
    if current_lock_state != LOCKED_PENDING:
        return {
            "account_id": account_id,
            "applied": False,
            "reason": "release_email only applies to locked_pending",
        }
    return {
        "account_id": account_id,
        "applied": True,
        "from_state": LOCKED_PENDING,
        "to_state": ACTIVE,
        "action": "release_email",
        "via": "help_center",
    }
