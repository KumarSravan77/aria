from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os
import time
import requests


@dataclass
class ThanosAgent:
    """Long-term and multi-cluster metrics investigation agent."""

    thanos_url: str | None = None
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        self.thanos_url = self.thanos_url or os.getenv("THANOS_URL") or os.getenv("THANOS_QUERY_URL")

    def query(self, promql: str) -> dict[str, Any]:
        if not self.thanos_url:
            return {
                "available": False,
                "reason": "THANOS_URL_not_configured",
                "query": promql,
                "summary": "Thanos unavailable; configure THANOS_URL for long-term metrics",
            }
        try:
            response = requests.get(f"{self.thanos_url.rstrip('/')}/api/v1/query", params={"query": promql}, timeout=self.timeout_seconds)
            return {"available": response.ok, "status_code": response.status_code, "query": promql, "data": response.json() if response.ok else response.text[:500]}
        except Exception as exc:
            return {"available": False, "query": promql, "error": str(exc)}

    def query_range(self, promql: str, start: int | None = None, end: int | None = None, step: str = "5m") -> dict[str, Any]:
        if not self.thanos_url:
            return {
                "available": False,
                "reason": "THANOS_URL_not_configured",
                "query": promql,
                "summary": "Thanos range query unavailable",
            }
        end = end or int(time.time())
        start = start or end - 7 * 24 * 3600
        try:
            response = requests.get(
                f"{self.thanos_url.rstrip('/')}/api/v1/query_range",
                params={"query": promql, "start": start, "end": end, "step": step},
                timeout=self.timeout_seconds,
            )
            return {"available": response.ok, "status_code": response.status_code, "query": promql, "start": start, "end": end, "step": step, "data": response.json() if response.ok else response.text[:500]}
        except Exception as exc:
            return {"available": False, "query": promql, "error": str(exc)}

    def run(self, incident: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        service = incident.get("service") or incident.get("target") or context.get("service") or "unknown"
        window = str(incident.get("window") or context.get("window") or "7d")
        latency_query = f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le))'
        error_query = f'sum(rate(http_requests_total{{service="{service}",status=~"5.."}}[5m]))'
        latency = self.query_range(latency_query)
        errors = self.query_range(error_query)
        return {
            "agent": "thanos",
            "type": "long_term_metrics_evidence",
            "service": service,
            "window": window,
            "latency": latency,
            "errors": errors,
            "summary": "Thanos historical metrics queried for incident pattern comparison",
            "available": latency.get("available", False) or errors.get("available", False),
            "safety_boundary": "read-only metrics diagnostics",
        }
