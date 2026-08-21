from flask import Blueprint, abort, request

from accounts.help_center import HelpCenterError, release_email

bp = Blueprint("operator_help", __name__, url_prefix="/account/help")


@bp.get("/")
def help_menu():
    return {
        "title": "Extra / Help",
        "actions": [
            {
                "id": "release_email",
                "label": "Release email",
                "method": "POST",
                "path": "/account/help/release-email",
            }
        ],
    }


@bp.post("/release-email")
def release_email_view():
    account_id = request.form.get("account_id") or request.json["account_id"]
    lock_state = request.form.get("lock_state") or request.json["lock_state"]
    try:
        return release_email(account_id, lock_state)
    except HelpCenterError:
        abort(409)
