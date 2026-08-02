from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class ObservabilityStandardsAgent:
    name = "observability-standards-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        obs = service_profile.get("observability", {}) or {}
        findings: List[Finding] = []
        checks = [
            ("metrics", "obs-missing-metrics", "metrics collection missing", "P1"),
            ("logs", "obs-missing-logs", "structured logs missing", "P1"),
            ("traces", "obs-missing-traces", "distributed traces missing", "P1"),
            ("dashboards", "obs-missing-dashboards", "service dashboard missing", "P2"),
            ("alerts", "obs-missing-alerts", "actionable alerts missing", "P2"),
            ("correlation_id", "obs-missing-correlation-id", "correlation ID standard missing", "P2"),
        ]
        for key, fid, title, sev in checks:
            if not obs.get(key):
                findings.append(Finding(
                    id=fid,
                    title=f"Observability standards gap: {title}",
                    category="observability",
                    severity=sev,
                    evidence=[Evidence("service_profile", f"observability.{key}", str(obs.get(key)), "true", collector=self.name)],
                    impact={"user_impact":"Issues may take longer to detect or troubleshoot.","business_impact":"MTTD/MTTR and audit readiness may be reduced.","technical_impact":"Required telemetry signal or operational view is missing."},
                    recommendation={"summary":f"Enable {key} using the ARIA observability golden path.","remediation_type":"auto_fix_candidate"},
                    confidence={"score":0.82,"explanation":"Missing observability standard in service profile."},
                ))
        return findings
