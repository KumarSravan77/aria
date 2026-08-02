from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class SecurityGovernanceAgent:
    name = "security-governance-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        sec = service_profile.get("security", {}) or {}
        findings: List[Finding] = []
        checks = [
            ("rbac_least_privilege", "sec-rbac-not-least-privilege", "RBAC least privilege not confirmed", "P1"),
            ("network_policy", "sec-missing-network-policy", "NetworkPolicy missing", "P1"),
            ("pod_security_context", "sec-missing-pod-security-context", "pod securityContext missing", "P1"),
            ("secret_management", "sec-missing-secret-management", "approved secret management missing", "P1"),
            ("image_scan", "sec-missing-image-scan", "container image scan missing", "P1"),
            ("policy_as_code", "sec-missing-policy-as-code", "policy-as-code validation missing", "P2"),
        ]
        for key, fid, title, sev in checks:
            if not sec.get(key):
                findings.append(Finding(
                    id=fid,
                    title=f"Security governance gap: {title}",
                    category="security",
                    severity=sev,
                    evidence=[Evidence("service_profile", f"security.{key}", str(sec.get(key)), "true", collector=self.name)],
                    impact={"user_impact":"Security weakness may expose service or data.","business_impact":"Compliance and audit risk may increase.","technical_impact":"Required security control is not declared."},
                    recommendation={"summary":f"Implement {key} using ARIA DevSecOps standards.","remediation_type":"approval_required" if sev == "P1" else "auto_fix_candidate"},
                    confidence={"score":0.81,"explanation":"Security profile missing required governance control."},
                ))
        return findings
