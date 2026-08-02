from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class SecurityReasoner:
    def analyze(self, event: dict[str, Any], deployment_context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = str(event).lower()
        hypotheses = []
        if "privileged" in text:
            hypotheses.append("privileged_container_policy_violation")
        if "shell" in text or "exec" in text:
            hypotheses.append("suspicious_runtime_execution")
        if "cve" in text or "vulnerability" in text:
            hypotheses.append("vulnerable_image_deployed")
        if deployment_context:
            hypotheses.append("recent_deployment_context_available")
        return {
            "hypotheses": hypotheses or ["unknown_security_event"],
            "recommended_action": "contain_and_investigate",
            "requires_approval": True,
            "safety_boundary": "containment recommendations require policy and approval gates",
        }
