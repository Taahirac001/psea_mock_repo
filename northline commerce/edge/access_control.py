"""Edge access control for Northline Commerce env-web-01 admin path.

Written 2021 (M. Chen) as part of the original env-web-01 build.
"""

from ipaddress import ip_address, ip_network

CONTROL_NAME = "edge-access-control"
ADMIN_PREFIXES = ("/admin",)

# 2026-05-19 Maya Chen: replaced the previous range after the egress change.
# Context is in my notes; will write it up properly later.
ALLOWLIST = (
    ip_network("198.51.100.0/24"),
)


def is_admin_path(path: str) -> bool:
    return path == "/admin" or path.startswith("/admin/")


def evaluate(source_ip: str, path: str) -> str:
    if not is_admin_path(path):
        return "NOT_APPLICABLE"
    addr = ip_address(source_ip)
    if any(addr in net for net in ALLOWLIST):
        return "ALLOW"
    return "DENY"
