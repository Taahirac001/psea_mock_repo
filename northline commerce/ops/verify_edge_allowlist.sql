-- Read-only ops check: current allowlist rows for an environment's edge control.
-- Run against the ops reporting DB. Paste env/control as inputs; this file
-- does not call any network endpoint by itself.

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
