from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TraceCausalityEngine:
    def infer(self, evidence: list[dict[str, Any]]) -> dict[str, Any]:
        text = " ".join(str(e).lower() for e in evidence)
        causes = []
        confidence = 0.3
        if "deployment" in text and ("latency" in text or "error" in text):
            causes.append("possible_deployment_regression")
            confidence += 0.35
        if "database" in text or "db_timeout" in text:
            causes.append("possible_database_dependency")
            confidence += 0.2
        if "dns" in text:
            causes.append("possible_service_discovery_issue")
            confidence += 0.2
        return {
            "causal_hypotheses": causes or ["insufficient_evidence"],
            "confidence": round(min(confidence, 0.95), 2),
            "safety_boundary": "causal inference is advisory; remediation still requires ReBAC, policy and approval",
        }
