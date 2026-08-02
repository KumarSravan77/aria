from __future__ import annotations
from typing import Any


# Default on-call chains per service. In production, pull from PagerDuty API.
DEFAULT_ONCALL_CHAINS: dict[str, list[str]] = {
    "checkout-api":   ["sre-primary", "sre-secondary", "eng-lead", "vp-engineering"],
    "payment-api":    ["payments-sre", "payments-lead", "vp-engineering"],
    "kubernetes-platform": ["platform-sre", "platform-lead", "cto"],
    "default":        ["on-call-primary", "on-call-secondary", "incident-commander"],
}

# Simulated concurrent incidents per responder (triggers bottleneck detection)
RESPONDER_LOAD: dict[str, int] = {
    "sre-primary":   2,
    "sre-secondary": 1,
    "eng-lead":      4,
    "payments-sre":  3,
}
BOTTLENECK_THRESHOLD = 3


class PagerDutySimulator:
    """Simulates escalation paths and detects on-call bottlenecks.

    Uses static chains for demo/test. Wire to PagerDuty REST API in production.
    """

    def __init__(
        self,
        chains: dict[str, list[str]] | None = None,
        load: dict[str, int] | None = None,
    ) -> None:
        self._chains = chains or DEFAULT_ONCALL_CHAINS
        self._load = load or RESPONDER_LOAD

    def simulate_escalation(self, service: str, severity: str = "P1") -> dict[str, Any]:
        chain = self._chains.get(service) or self._chains["default"]
        steps = []
        bottlenecks = []
        for i, responder in enumerate(chain):
            load = self._load.get(responder, 0)
            is_bottleneck = load >= BOTTLENECK_THRESHOLD
            if is_bottleneck:
                bottlenecks.append(responder)
            steps.append({
                "level": i + 1,
                "responder": responder,
                "concurrent_incidents": load,
                "bottleneck_risk": is_bottleneck,
                "estimated_response_minutes": (i + 1) * 5 + (load * 2),
            })

        paged_count = 1 if severity == "P1" else max(1, len(chain) // 2)
        return {
            "service": service,
            "severity": severity,
            "escalation_chain": steps,
            "bottlenecks_detected": bottlenecks,
            "paging_saturation_risk": len(bottlenecks) >= 2,
            "recommended_paged_count": paged_count,
            "recommendation": (
                f"Bottleneck risk at {bottlenecks}. Consider cross-training or capacity increase."
                if bottlenecks else "Escalation chain healthy."
            ),
        }
