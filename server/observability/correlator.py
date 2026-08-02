from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ObservabilityCorrelator:
    """Joins metrics, logs, traces and topology into one evidence object.

    This class is intentionally defensive: every backend can be unavailable and
    the caller still receives a structured response for the incident timeline.
    """
    prometheus: Any
    loki: Any
    tempo: Any
    hubble: Any | None = None

    def correlate(self, service: str, window_minutes: int = 30, deployment: dict | None = None) -> dict:
        metrics = self._safe("metrics", lambda: self.prometheus.query(f'rate(http_requests_total{{service="{service}"}}[5m])'))
        latency = self._safe("latency", lambda: self.prometheus.query(f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m]))'))
        logs = self._safe("logs", lambda: self.loki.query(f'{{app="{service}"}} |= "error"'))
        traces = self._safe("traces", lambda: self.tempo.search_service_traces(service))
        topology = self._safe("topology", lambda: self.hubble.service_topology(service)) if self.hubble else {"available": False}

        evidence = []
        for name, item in [("metrics", metrics), ("latency", latency), ("logs", logs), ("traces", traces), ("topology", topology)]:
            evidence.append({
                "source": name,
                "available": bool(item.get("available", True)) if isinstance(item, dict) else True,
                "summary": self._summarize(name, item),
                "raw": item,
            })

        probable = self._infer_probable_cause(evidence, deployment or {})
        return {
            "service": service,
            "window_minutes": window_minutes,
            "deployment": deployment or {},
            "evidence": evidence,
            "probable_cause": probable["cause"],
            "confidence": probable["confidence"],
            "narrative": probable["narrative"],
            "guardrail": "Evidence is correlation input only. AI can recommend; policy/ReBAC/approval own execution.",
        }

    def _safe(self, source: str, fn):
        try:
            value = fn()
            if isinstance(value, dict):
                return value
            return {"available": True, "value": value}
        except Exception as exc:
            return {"available": False, "source": source, "error": str(exc)}

    def _summarize(self, name: str, item: Any) -> str:
        if isinstance(item, dict) and item.get("available") is False:
            return f"{name} unavailable: {item.get('reason') or item.get('error') or 'not configured'}"
        if name == "logs":
            return "Log evidence collected for error-pattern correlation."
        if name == "traces":
            return "Trace evidence collected for slow-span/downstream correlation."
        if name == "latency":
            return "Latency query executed for p95 correlation."
        if name == "metrics":
            return "Request-rate/error-rate query executed for symptom correlation."
        return f"{name} evidence collected."

    def _infer_probable_cause(self, evidence: list[dict], deployment: dict) -> dict:
        if deployment.get("recent_deployment") or deployment.get("revision"):
            return {
                "cause": "possible_deployment_regression",
                "confidence": 0.72,
                "narrative": "A recent deployment/change exists in the same investigation window; compare metrics/logs/traces before and after the revision.",
            }
        unavailable = [e["source"] for e in evidence if not e.get("available")]
        if len(unavailable) >= 3:
            return {
                "cause": "insufficient_observability_evidence",
                "confidence": 0.35,
                "narrative": f"Multiple telemetry backends are unavailable: {', '.join(unavailable)}. Continue deterministic checks before recommending remediation.",
            }
        return {
            "cause": "needs_human_correlation",
            "confidence": 0.55,
            "narrative": "Telemetry was collected, but no single source dominates. Use RAG runbooks and timeline changes to continue investigation.",
        }
