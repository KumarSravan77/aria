from __future__ import annotations
from server.agents.base import BaseAgent, AgentResult
from server.observability.prometheus_client import PrometheusClient

class MetricsAgent(BaseAgent):
    name = "metrics"
    def __init__(self, prometheus: PrometheusClient):
        self.prometheus = prometheus
    def run(self, incident: dict, context: dict | None = None) -> AgentResult:
        service = incident.get("service", "unknown")
        metric = self.prometheus.query(f'rate(http_requests_total{{service="{service}"}}[5m])')
        return AgentResult(
            agent=self.name,
            available=bool(metric.get("available", False)),
            summary="Collected service metric signal" if metric.get("available") else "Prometheus unavailable; using incident payload signals",
            evidence=[{"type":"prometheus", "service":service, "result":metric}],
            recommendations=["Validate error rate, p95 latency, and saturation before remediation"],
        )
