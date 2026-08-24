# env-web-01 — Northline Commerce (sanitized)

Web environment for Northline Commerce. Built by our platform team in 2021
and operated by us since. Northline does not run or administer this stack.

| Path | What it is |
|---|---|
| `edge/access_control.py` | Edge control for the `/admin` path — support allowlist plus vault-backed session verification |
| `edge/admin_gate.py` | Admin sign-in gate — retrieves the admin credential from the internal vault (fail-closed) |
| `deploy/env-web-01.yml` | Deploy descriptor (edge + origin + secrets store) |
| `config/service_map.yml` | How edge, app, and vault relate |
| `ops/verify_edge_allowlist.sql` | Read-only ops check of deployed allowlist rows |

Admin credentials are vault-only. Nothing in this repo contains or caches a
credential.

If you need to touch the edge rule or the vault integration, talk to
**Maya Chen** first — she built both and the write-up is still on her list.

Do not commit credentials here.
