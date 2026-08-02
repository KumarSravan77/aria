from __future__ import annotations

import os
import time
from dataclasses import dataclass, asdict
from typing import Protocol


@dataclass(frozen=True)
class SecretRequest:
    service_id: str
    environment: str
    secret_ref: str
    purpose: str
    requester: str = "aria"


@dataclass(frozen=True)
class SecretLease:
    secret_ref: str
    provider: str
    lease_id: str
    ttl_seconds: int
    expires_at_epoch: int
    value_available: bool
    metadata: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


class SecretProvider(Protocol):
    name: str

    def issue_lease(self, request: SecretRequest) -> SecretLease: ...


class VaultSecretProvider:
    """Safe Vault adapter skeleton.

    This intentionally returns leases/metadata only. ARIA agents should not print or persist raw secret values.
    A production implementation can exchange Kubernetes/JWT/OIDC auth for short-lived Vault leases here.
    """

    name = "vault"

    def __init__(self, address: str | None = None, mount: str = "kv") -> None:
        self.address = address or os.getenv("VAULT_ADDR", "http://vault.vault.svc:8200")
        self.mount = mount

    def issue_lease(self, request: SecretRequest) -> SecretLease:
        now = int(time.time())
        lease_id = f"vault:{request.environment}:{request.service_id}:{request.secret_ref}"
        return SecretLease(
            secret_ref=request.secret_ref,
            provider=self.name,
            lease_id=lease_id,
            ttl_seconds=900,
            expires_at_epoch=now + 900,
            value_available=False,
            metadata={
                "vault_addr": self.address,
                "mount": self.mount,
                "service_id": request.service_id,
                "environment": request.environment,
                "purpose": request.purpose,
                "policy": f"aria-{request.service_id}-{request.environment}",
            },
        )


class SecretBroker:
    """Central gateway for secret access used by agents, CI/CD, and K8s integrations."""

    def __init__(self, provider: SecretProvider | None = None) -> None:
        self.provider = provider or VaultSecretProvider()

    def request_secret_lease(self, request: SecretRequest) -> dict:
        if not request.service_id or not request.environment or not request.secret_ref:
            raise ValueError("service_id, environment, and secret_ref are required")
        lease = self.provider.issue_lease(request)
        return {
            "status": "lease_issued",
            "raw_secret_returned": False,
            "lease": lease.to_dict(),
            "safety": {
                "prompt_safe": True,
                "store_raw_secret": False,
                "redact_before_rag": True,
                "recommended_injection": "external-secrets-operator",
            },
        }
