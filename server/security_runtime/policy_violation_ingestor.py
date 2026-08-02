from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class PolicyViolationIngestor:
    """Normalizes Kyverno/Gatekeeper PolicyReport-like payloads into ARIA incidents."""

    def normalize_kyverno(self, payload: dict[str, Any]) -> list[dict]:
        return self._normalize(payload, source="kyverno", default_alert="KyvernoPolicyViolation")

    def normalize_gatekeeper(self, payload: dict[str, Any]) -> list[dict]:
        return self._normalize(payload, source="gatekeeper", default_alert="GatekeeperConstraintViolation")

    def _normalize(self, payload: dict[str, Any], source: str, default_alert: str) -> list[dict]:
        results = payload.get("results") or payload.get("items") or [payload]
        incidents = []
        for idx, item in enumerate(results):
            resource = item.get("resource") or item.get("resources", [{}])[0] if isinstance(item, dict) else {}
            service = item.get("service") or item.get("app") or resource.get("name") or payload.get("service") or "unknown"
            namespace = item.get("namespace") or resource.get("namespace") or payload.get("namespace") or "default"
            policy = item.get("policy") or item.get("policyName") or item.get("constraint") or payload.get("policy") or "unknown-policy"
            severity = item.get("severity") or payload.get("severity") or "P2"
            incidents.append({
                "incident_id": item.get("incident_id") or f"{source.upper()}-{policy}-{service}-{idx}",
                "alert_name": default_alert,
                "source": source,
                "service": service,
                "namespace": namespace,
                "environment": payload.get("environment", "prod"),
                "severity": severity,
                "symptoms": [f"{source} policy violation: {policy}"],
                "policy": policy,
                "message": item.get("message") or item.get("reason") or "Policy violation detected",
                "payload": item,
            })
        return incidents
