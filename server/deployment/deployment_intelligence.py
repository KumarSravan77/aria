from __future__ import annotations
from typing import Any

class DeploymentIntelligence:
    def correlate(self, incident: dict[str, Any], deployments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        service = incident.get("service", "unknown")
        deployments = deployments or incident.get("signals", {}).get("recent_deployments", []) or []
        related = [d for d in deployments if d.get("service") in {service, None}]
        suspicion = "high" if related and any(s in incident.get("symptoms", []) for s in ["high latency", "increased 5xx", "errors"]) else "low"
        return {"service": service, "recent_deployments": related, "deployment_correlation": suspicion, "recommendation": "Compare before/after metrics and consider GitOps rollback if regression is confirmed"}
