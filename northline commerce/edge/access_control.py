"""Edge access control for Northline Commerce env-web-01 admin path.

The Confluence runbook "Northline Commerce — Edge access control" still lists
203.0.113.0/24. This file is what is actually deployed.
"""

from ipaddress import ip_address, ip_network

CONTROL_NAME = "edge-access-control"
ADMIN_PREFIXES = ("/admin",)

# Maya Chen changed this on 2026-05-19. The support NAT moved.
# Documented CIDR on the runbook page was never updated.
ALLOWLIST = (
    ip_network("198.51.100.0/24"),
)

# Vault is the live secret store. Spreadsheet in the access doc is stale.
VAULT_SECRET_PATH = "secret/clients/northline/env-web-01/admin"


def is_admin_path(path: str) -> bool:
    return path == "/admin" or path.startswith("/admin/")


def evaluate(source_ip: str, path: str) -> str:
    if not is_admin_path(path):
        return "NOT_APPLICABLE"
    addr = ip_address(source_ip)
    if any(addr in net for net in ALLOWLIST):
        return "ALLOW"
    return "DENY"
