from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class GraphRouter:
    def select_mode(self, active_incidents: int = 0) -> str:
        if active_incidents >= 50:
            return "SURVIVAL"
        if active_incidents >= 10:
            return "DEGRADED"
        return "NORMAL"

    def route(self, incident: dict[str, Any], active_incidents: int = 0) -> list[str]:
        mode = self.select_mode(active_incidents)
        severity = str(incident.get("severity", "P3")).upper()
        text = " ".join(str(v).lower() for v in incident.values())
        signals = " ".join(str(x).lower() for x in incident.get("signals", []))
        combined = f"{text} {signals}"

        if mode == "SURVIVAL":
            return ["metrics", "logs"]

        if any(x in combined for x in ["crashloop", "oom", "pending", "evicted", "imagepull", "nodenotready", "probe"]):
            route = ["metrics", "logs", "kubernetes_troubleshooter", "rag", "rca"]
        elif "deployment" in combined or "rollout" in combined:
            route = ["metrics", "traces", "rag", "rca", "healing"]
        elif severity in {"P1", "CRITICAL"}:
            route = ["metrics", "logs", "traces", "kubernetes_troubleshooter", "rag", "security", "healing", "rca", "chatops"]
        elif severity == "P2":
            route = ["metrics", "logs", "traces", "rag", "rca"]
        else:
            route = ["metrics", "logs"]

        service_mesh_terms = ["istio", "mtls", "virtualservice", "destinationrule", "sidecar", "envoy", "canary"]
        historical_terms = ["historical", "trend", "thanos", "last 7 days", "last 30 days", "slo trend"]
        streaming_terms = ["kafka", "consumer lag", "lag", "rebalance", "topic", "partition", "isr", "broker", "streaming"]

        if any(term in combined for term in service_mesh_terms) and "istio" not in route:
            route.append("istio")
        if any(term in combined for term in historical_terms) and "thanos" not in route:
            route.append("thanos")
        if any(term in combined for term in streaming_terms) and "kafka" not in route:
            route.append("kafka")

        if mode == "DEGRADED":
            return [n for n in route if n in {"metrics", "logs", "rag", "rca", "kubernetes_troubleshooter", "istio", "kafka"}]
        return route
