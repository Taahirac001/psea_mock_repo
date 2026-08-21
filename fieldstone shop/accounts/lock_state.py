ACTIVE = "active"
LOCKED_PENDING = "locked_pending"


def can_change_password(lock_state: str) -> bool:
    return lock_state == ACTIVE
