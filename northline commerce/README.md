# env-web-01 — Northline Commerce

Sanitized fixture for a NamiFlow walkthrough. No real client, no secrets.

| Path | What Nami should be able to find |
|---|---|
| `edge/access_control.py` | Deployed allowlist `198.51.100.0/24` (contradicts Confluence) |
| `deploy/env-web-01.yml` | Same allowlist + vault path + owner TBD / Maya Chen |
| `ops/verify_edge_allowlist.sql` | On-call verification query (manual; values are inputs) |
| `config/service_map.yml` | How edge, vault, and app relate |

If you need production admin access, ask **Maya Chen**. She knows the vault path and why the edge allowlist looks the way it does.

Do not commit credentials here.
