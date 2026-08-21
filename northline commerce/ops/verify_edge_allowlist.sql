-- On-call verification for Northline Commerce env-web-01 edge allowlist.
-- Run against the ops reporting DB (read-only). Paste host/env as inputs;
-- this file does not call any network endpoint by itself.
--
-- Expected: rows should match what is DEPLOYED (see edge/access_control.py),
-- not what the Confluence runbook still documents (203.0.113.0/24).

SELECT
    environment,
    control_name,
    cidr_block,
    updated_at,
    updated_by
FROM edge_allowlist_rules
WHERE environment = :env_name          -- e.g. 'env-web-01'
  AND control_name = 'edge-access-control'
ORDER BY updated_at DESC;
