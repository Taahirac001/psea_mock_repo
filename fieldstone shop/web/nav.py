"""Account-site operator navigation for env-acct-01.

These labels must match what you say in the room.
"""

OPERATOR_NAV = [
    {"id": "account", "label": "Account"},
    {
        "id": "extra_help",
        "label": "Extra / Help",
        "parent": "account",
        "items": [
            {"id": "release_email", "label": "Release email"},
        ],
    },
]


def release_email_path() -> str:
    return "Account → Extra / Help → Release email"
