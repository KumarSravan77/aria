from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class CICDStandardsAgent:
    name = "cicd-standards-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        cicd = service_profile.get("cicd", {}) or {}
        findings: List[Finding] = []
        standards = [
            ("build", "cicd-missing-build", "build stage missing", "P1"),
            ("unit_tests", "cicd-missing-unit-tests", "unit tests missing", "P1"),
            ("security_scan", "cicd-missing-security-scan", "security scan missing", "P1"),
            ("sbom", "cicd-missing-sbom", "SBOM generation missing", "P2"),
            ("artifact_signing", "cicd-missing-artifact-signing", "artifact/image signing missing", "P2"),
            ("rollback", "cicd-missing-rollback", "rollback automation missing", "P1"),
            ("deployment_strategy", "cicd-missing-safe-deployment", "safe deployment strategy missing", "P2"),
        ]
        for key, fid, title, sev in standards:
            if not cicd.get(key):
                findings.append(Finding(
                    id=fid,
                    title=f"CI/CD standards gap: {title}",
                    category="cicd",
                    severity=sev,
                    evidence=[Evidence("service_profile", f"cicd.{key}", str(cicd.get(key)), "configured", collector=self.name)],
                    impact={"user_impact":"Bad changes may reach users or be slower to recover.","business_impact":"Deployment risk and compliance gaps may increase.","technical_impact":"Pipeline lacks required platform control."},
                    recommendation={"summary":f"Add {key} to the CI/CD golden pipeline template.","remediation_type":"auto_fix_candidate"},
                    confidence={"score":0.84,"explanation":"CI/CD profile missing required standard."},
                ))
        return findings
