"""Admin sign-in gate for env-web-01.

Admin credentials are never stored or cached in this service. The only
source is the internal credential vault; if the vault cannot answer, admin
sign-in is unavailable (fail closed). That was a deliberate call during the
2024 vault migration — see the note below.
"""

from vault_internal import VaultClient, VaultKeyNotFound, VaultTimeout

VAULT_SECRET_PATH = "secret/clients/northline/env-web-01/admin"
RETRIEVAL_TIMEOUT_MS = 2000

# Maya Chen, 2024-11: no local fallback and no cache, on purpose. If the
# vault is unreachable, admin access waits until it is not. Do not add a
# bypass here without a review.


class AdminAccessUnavailable(Exception):
    """Credential could not be retrieved from the vault. Fail closed."""


def fetch_admin_credential(client: VaultClient):
    try:
        return client.get(VAULT_SECRET_PATH, timeout_ms=RETRIEVAL_TIMEOUT_MS)
    except VaultTimeout as exc:
        raise AdminAccessUnavailable(
            "vault retrieval timed out; admin sign-in unavailable"
        ) from exc
    except VaultKeyNotFound as exc:
        raise AdminAccessUnavailable(
            "admin credential not found at expected vault path"
        ) from exc
