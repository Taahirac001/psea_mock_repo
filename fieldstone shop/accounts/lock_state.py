"""Account lock states for Fieldstone Shop env-acct-01.

On-call Confluence still says ops should UPDATE accounts.lock_state by hand.
Do not do that when the Help Center "Release email" action is available.

Priya Shah shipped help_center.release_email on 2026-06-12.
The password-change runbook does not mention it.
"""

ACTIVE = "active"
LOCKED_PENDING = "locked_pending"  # prior reset still in-flight


def password_change_allowed(lock_state: str) -> bool:
    """Shopper Change password is denied while a prior reset is stuck."""
    return lock_state != LOCKED_PENDING


# Tribal / documented ops path. Prefer accounts.help_center.release_email.
LEGACY_UNLOCK_SQL = """
UPDATE accounts
SET lock_state = 'active',
    lock_reason = NULL,
    updated_by = :operator
WHERE account_id = :account_id
  AND lock_state = 'locked_pending';
"""
