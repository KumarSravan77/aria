from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class DevSecOpsAgent:
    """Validates standard security tooling is bound to each service/application."""

    name = "devsecops-agent"

    REQUIRED = [
        ("sast", "devsecops-missing-sast", "SAST missing", "Semgrep/SonarQube"),
        ("sca", "devsecops-missing-sca", "dependency/SCA scanning missing", "Dependabot/Snyk"),
        ("container_scan", "devsecops-missing-container-scan", "container scanning missing", "Trivy/Grype"),
        ("secret_scan", "devsecops-missing-secret-scan", "secret scanning missing", "Gitleaks/TruffleHog"),
        ("iac_scan", "devsecops-missing-iac-scan", "IaC scanning missing", "Checkov/tfsec"),
        ("sbom", "devsecops-missing-sbom", "SBOM generation missing", "Syft"),
        ("image_signing", "devsecops-missing-image-signing", "image signing missing", "Cosign"),
        ("policy_as_code", "devsecops-missing-policy-as-code", "policy-as-code missing", "OPA/Conftest"),
        ("admission_policy", "devsecops-missing-admission-policy", "admission policy missing", "Kyverno/Gatekeeper"),
        ("runtime_detection", "devsecops-missing-runtime-detection", "runtime security detection missing", "Falco"),
        ("security_gate_before_deploy", "devsecops-missing-release-gate", "security gate before deploy missing", True),
    ]

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        devsecops = service_profile.get("devsecops", {}) or {}
        findings: List[Finding] = []
        for key, fid, title, expected in self.REQUIRED:
            if not devsecops.get(key):
                findings.append(Finding(
                    id=fid,
                    title=f"DevSecOps standards gap: {title}",
                    category="devsecops",
                    severity="P1" if key in {"sast", "secret_scan", "container_scan", "security_gate_before_deploy"} else "P2",
                    evidence=[Evidence("service_profile", f"devsecops.{key}", str(devsecops.get(key)), str(expected), collector=self.name)],
                    impact={
                        "user_impact": "Unsafe code, images, or infrastructure changes may reach users.",
                        "business_impact": "Compliance, audit, and breach risk may increase.",
                        "technical_impact": "Required DevSecOps control is not wired into the service lifecycle.",
                    },
                    recommendation={"summary": f"Enable {key} in the shared ARIA DevSecOps pipeline/gate.", "remediation_type": "auto_fix_candidate"},
                    confidence={"score": 0.85, "explanation": "Service profile missing a required DevSecOps tool/control."},
                ))
        return findings
