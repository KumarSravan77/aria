from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

from .redaction import SecretRedactor


@dataclass(frozen=True)
class SecretFinding:
    title: str
    severity: str
    category: str
    evidence: str
    recommendation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class SecretGovernanceAgent:
    """Detects secret-risk patterns in repo, CI/CD, K8s, RAG, and telemetry inputs."""

    def __init__(self) -> None:
        self.redactor = SecretRedactor()

    def review(self, payload: dict[str, Any]) -> dict[str, Any]:
        findings: list[SecretFinding] = []
        text_blobs = self._collect_text(payload)
        combined = "\n".join(text_blobs)
        redacted = self.redactor.redact_text(combined)

        if redacted.redactions:
            findings.append(SecretFinding(
                title="Potential secret material detected in input",
                severity="P1",
                category="secrets",
                evidence=", ".join(f"{r['type']}={r['count']}" for r in redacted.redactions),
                recommendation="Block indexing/logging of this payload, rotate exposed credentials if committed, and rerun with redacted data.",
            ))

        if self._contains_static_ci_secret(payload):
            findings.append(SecretFinding(
                title="Static CI/CD secret reference detected",
                severity="P2",
                category="cicd",
                evidence="Pipeline appears to rely on long-lived secrets instead of OIDC/Vault federation.",
                recommendation="Use GitHub Actions/Jenkins OIDC to exchange identity for short-lived Vault/cloud credentials.",
            ))

        if self._k8s_env_secret_risk(payload):
            findings.append(SecretFinding(
                title="Kubernetes workload may expose secrets through environment variables",
                severity="P2",
                category="kubernetes",
                evidence="Workload uses secretKeyRef/env-style injection.",
                recommendation="Prefer External Secrets Operator with least-privilege SecretStore and avoid printing env vars in logs.",
            ))

        score = "A" if not findings else ("C" if any(f.severity == "P1" for f in findings) else "B")
        return {
            "agent": "secret-governance-agent",
            "score": score,
            "findings": [f.to_dict() for f in findings],
            "sanitized_preview": redacted.text[:2000],
            "controls": [
                "never_store_raw_secrets",
                "redact_before_prompt",
                "redact_before_rag_indexing",
                "short_lived_credentials",
                "approval_required_for_secret_rotation",
            ],
        }

    def sanitize_for_rag(self, document: dict[str, Any]) -> dict[str, Any]:
        sanitized = self.redactor.redact_payload(document)
        return {"sanitized": sanitized, "rag_index_allowed": True, "raw_secret_retained": False}

    def _collect_text(self, value: Any) -> list[str]:
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            out: list[str] = []
            for key, val in value.items():
                out.append(str(key))
                out.extend(self._collect_text(val))
            return out
        if isinstance(value, list):
            out: list[str] = []
            for item in value:
                out.extend(self._collect_text(item))
            return out
        return [str(value)] if value is not None else []

    def _contains_static_ci_secret(self, payload: dict[str, Any]) -> bool:
        text = "\n".join(self._collect_text(payload))
        return bool(re.search(r"\$\{\{\s*secrets\.[A-Z0-9_]+\s*\}\}|withCredentials|credentialsId", text))

    def _k8s_env_secret_risk(self, payload: dict[str, Any]) -> bool:
        text = "\n".join(self._collect_text(payload))
        return "secretKeyRef" in text or "envFrom" in text and "secretRef" in text
