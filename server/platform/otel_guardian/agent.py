from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding, Score


class OTelGuardianAgent:
    """Audits OpenTelemetry instrumentation readiness and cost-risk patterns."""

    name = "otel-guardian-agent"

    def review(self, service_profile: Dict[str, Any]) -> Dict[str, Any]:
        obs = service_profile.get("observability", {}) or {}
        otel = obs.get("otel", {}) or {}
        findings: List[Finding] = []

        def add(fid: str, title: str, sev: str, path: str, observed: Any, expected: str, summary: str, cost: bool = False):
            findings.append(Finding(
                id=fid,
                title=title,
                category="observability",
                severity=sev,
                evidence=[Evidence(source="service_profile", path=path, observed=str(observed), expected=expected, collector=self.name)],
                impact={"user_impact":"Incidents may take longer to diagnose.","business_impact":"MTTR, auditability, or telemetry cost may be negatively affected.","technical_impact":"Telemetry does not meet ARIA OpenTelemetry standards."},
                recommendation={"summary":summary,"remediation_type":"auto_fix_candidate"},
                confidence={"score":0.84,"explanation":"Deterministic OTel profile audit." + (" Cost risk detected." if cost else "")},
            ))

        if not obs.get("otel_enabled"):
            add("otel-disabled", "OpenTelemetry Guardian: instrumentation is not enabled", "P1", "observability.otel_enabled", obs.get("otel_enabled"), "true", "Enable OpenTelemetry instrumentation using the language golden path.")
        if not otel.get("service_name"):
            add("otel-missing-service-name", "OpenTelemetry Guardian: service.name resource attribute missing", "P1", "observability.otel.service_name", otel.get("service_name"), "non-empty", "Set OTEL_SERVICE_NAME or resource.service.name consistently.")
        if not otel.get("trace_context_propagation", obs.get("trace_context_propagation")):
            add("otel-missing-context-propagation", "OpenTelemetry Guardian: trace context propagation missing", "P2", "observability.otel.trace_context_propagation", otel.get("trace_context_propagation", obs.get("trace_context_propagation")), "true", "Enable W3C tracecontext propagation across ingress, service mesh, and app clients.")
        if otel.get("high_cardinality_attributes"):
            add("otel-high-cardinality-risk", "OpenTelemetry Guardian: high-cardinality attributes detected", "P1", "observability.otel.high_cardinality_attributes", otel.get("high_cardinality_attributes"), "empty list", "Remove user/session/request-id style labels from metrics and span dimensions; keep them in logs/traces only when governed.", cost=True)
        if not otel.get("collector") and obs.get("otel_enabled"):
            add("otel-collector-missing", "OpenTelemetry Guardian: collector path not defined", "P2", "observability.otel.collector", otel.get("collector"), "defined", "Route telemetry through an OTel Collector for sampling, filtering, and export governance.")

        numeric = max(0, 100 - sum({"P0":35,"P1":20,"P2":10,"P3":5,"INFO":0}[f.severity] for f in findings))
        grade = "A" if numeric >= 90 else "B" if numeric >= 75 else "C" if numeric >= 60 else "D" if numeric >= 45 else "F"
        return {"score": Score("otel_guardian", grade, numeric, "OTel score from instrumentation, semantic, propagation, and cost-risk checks.", [f.id for f in findings if f.severity in ("P0","P1")]), "findings": findings}
