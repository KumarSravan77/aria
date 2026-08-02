from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class CanaryPlanner:
    """Safe canary planner. It recommends rollout steps; Argo Rollouts/Argo CD execute only after approval."""

    default_steps: tuple[int, ...] = (10, 25, 50, 75, 100)

    def plan(self, service: str, namespace: str = "demo", strategy: str = "canary", traffic_steps: list[int] | None = None) -> dict[str, Any]:
        steps = traffic_steps or list(self.default_steps)
        if strategy not in {"canary", "blue_green"}:
            return {"available": False, "reason": f"Unsupported strategy: {strategy}", "service": service}
        return {
            "available": True,
            "service": service,
            "namespace": namespace,
            "strategy": strategy,
            "traffic_steps": steps,
            "analysis": {
                "provider": "prometheus",
                "checks": [
                    "p95 latency must stay below threshold",
                    "5xx error rate must stay below threshold",
                    "availability SLO burn must not exceed budget",
                ],
            },
            "safety_boundary": "Planner only recommends rollout policy. Argo Rollouts/Argo CD execution still requires ReBAC, policy, approval, and audit.",
        }
