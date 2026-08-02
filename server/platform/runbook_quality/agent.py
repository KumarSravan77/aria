from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class RunbookQualityAgent:
    name = "runbook-quality-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        runbook = service_profile.get("runbook", {}) or {}
        findings: List[Finding] = []
        for key in ["owner", "escalation", "dashboards", "rollback_steps", "known_failure_modes"]:
            if not runbook.get(key):
                findings.append(Finding(
                    id=f"runbook-missing-{key.replace('_','-')}",
                    title=f"Runbook quality gap: {key.replace('_',' ')} missing",
                    category="runbook",
                    severity="P2" if key in ("rollback_steps", "escalation") else "P3",
                    evidence=[Evidence("service_profile", f"runbook.{key}", str(runbook.get(key)), "defined", collector=self.name)],
                    impact={"user_impact":"Incident response may be slower.","business_impact":"MTTR and operational handoff risk may increase.","technical_impact":"Runbook lacks required operational section."},
                    recommendation={"summary":f"Add {key.replace('_',' ')} to the service runbook.","remediation_type":"runbook"},
                    confidence={"score":0.8,"explanation":"Runbook metadata missing."},
                ))
        return findings
