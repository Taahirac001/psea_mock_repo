from accounts.lock_state import can_change_password


class PasswordChangeDenied(Exception):
    pass


def change_password(account_id: str, lock_state: str, new_password_hash: str) -> None:
    if not can_change_password(lock_state):
        raise PasswordChangeDenied(
            f"{account_id}: password change blocked while lock_state={lock_state}"
        )
    # persist new_password_hash — omitted in this module
