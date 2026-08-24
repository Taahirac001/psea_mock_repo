"""Edge access control for Northline Commerce env-web-01 admin path.

Written 2021 (M. Chen) as part of the original env-web-01 build.

Admin requests pass two checks: the source IP must be on the support
allowlist, and the edge must hold a current verifier key to sign the admin
session. The verifier key is not stored locally — it is fetched from the
internal credential vault.
"""

from ipaddress import ip_address, ip_network

from vault_internal import VaultClient, VaultKeyNotFound, VaultTimeout

CONTROL_NAME = "edge-access-control"
ADMIN_PREFIXES = ("/admin",)

# Support egress NAT range. Unchanged since the 2021 build.
ALLOWLIST = (
    ip_network("203.0.113.0/24"),
)

# The session verifier key lives only in the internal credential vault.
VERIFIER_KEY_PATH = "secret/clients/northline/env-web-01/edge-verifier"
KEY_FETCH_TIMEOUT_MS = 1500

# 2026-05-19 Maya Chen: verification is fail-closed now. If the verifier key
# cannot be fetched, admin requests are denied even from allowlisted IPs.
# Before this change the edge let allowlisted traffic through unverified when
# the vault did not answer. Context is in my notes; will write it up properly
# later.
FAIL_MODE = "closed"


def is_admin_path(path: str) -> bool:
    return path == "/admin" or path.startswith("/admin/")


def evaluate(source_ip: str, path: str, vault: VaultClient) -> str:
    if not is_admin_path(path):
        return "NOT_APPLICABLE"
    addr = ip_address(source_ip)
    if not any(addr in net for net in ALLOWLIST):
        return "DENY:not_in_allowlist"
    try:
        vault.get(VERIFIER_KEY_PATH, timeout_ms=KEY_FETCH_TIMEOUT_MS)
    except (VaultTimeout, VaultKeyNotFound):
        if FAIL_MODE == "closed":
            return "DENY:verifier_unavailable"
        return "ALLOW"
    return "ALLOW"
