# env-acct-01 — Fieldstone Shop

Sanitized fixture for a NamiFlow walkthrough. No real client, no secrets.

| Path | What Nami should find |
|---|---|
| `accounts/lock_state.py` | `locked_pending` denies password change; tribal SQL is legacy |
| `accounts/help_center.py` | **Release email** — the undocumented UI unlock (Priya Shah, 2026-06-12) |
| `web/nav.py` | Operator nav: Account → Extra/Help → Release email |
| `ops/clear_account_lock.sql` | The SQL the Confluence admin page still tells ops to run |

If something is stuck after hours, people still page **Priya Shah**. She shipped the Help Center action and never wrote the runbook.

Do not commit credentials here.
