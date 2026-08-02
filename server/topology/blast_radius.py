from __future__ import annotations
from typing import Any
from server.topology.dependency_graph import ServiceDependencyGraph

CUSTOMER_FACING_KEYWORDS = {"checkout", "api", "payment", "order", "gateway", "frontend"}
SEVERITY_MULTIPLIER = {"P1": 3, "P2": 2, "P3": 1, "P4": 1}


class BlastRadiusAnalyzer:
    """Computes the blast radius of a service failure using the dependency graph.

    Score = len(all_affected) × severity_multiplier.
    Impact level thresholds: critical≥9, high≥3, low<3.
    """

    def __init__(self, graph: ServiceDependencyGraph) -> None:
        self.graph = graph

    def analyze(self, service: str, severity: str = "P1") -> dict[str, Any]:
        direct = self.graph.downstream(service)
        all_affected = self.graph.all_affected(service)
        upstream = self.graph.upstream(service)
        customer_facing = [
            s for s in all_affected
            if any(kw in s.lower() for kw in CUSTOMER_FACING_KEYWORDS)
        ]

        multiplier = SEVERITY_MULTIPLIER.get(severity.upper(), 1)
        score = len(all_affected) * multiplier

        if score >= 9:
            impact = "critical"
        elif score >= 3:
            impact = "high"
        else:
            impact = "low"

        return {
            "root_service": service,
            "severity": severity,
            "direct_downstream": direct,
            "all_affected_services": all_affected,
            "upstream_callers": upstream,
            "customer_facing_impact": customer_facing,
            "blast_radius_score": score,
            "impact_level": impact,
            "recommendation": (
                f"Blast radius is {impact.upper()}. {len(all_affected)} service(s) affected. "
                + ("Escalate immediately and notify customer-facing teams." if impact == "critical"
                   else "Prioritize investigation above standard P2 workflows." if impact == "high"
                   else "Monitor downstream services for latency increase.")
            ),
        }
