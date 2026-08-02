from __future__ import annotations

from typing import Any, Dict, List

from server.platform.terraform_drift.runner import TerraformPlanRunner

from server.platform.spec_harness.models import Evidence, Finding, Score


class TerraformDriftAgent:
    """Independent Terraform/IaC drift analysis agent.

    This agent is intentionally not executed by the AI Service Review Agent.
    It can be called by onboarding, scheduled jobs, pre-release checks, or audit workflows.
    """

    name = "terraform-drift-agent"

    def __init__(self) -> None:
        self.runner = TerraformPlanRunner()

    def plan_commands(self, working_dir: str) -> Dict[str, Any]:
        return self.runner.build_commands(working_dir)

    def analyze(self, terraform_plan: Dict[str, Any], environment: str) -> Dict[str, Any]:
        findings: List[Finding] = []
        changes = terraform_plan.get("resource_changes", [])
        drifted = [c for c in changes if c.get("change", {}).get("actions") not in ([], ["no-op"], None)]

        for idx, change in enumerate(drifted):
            address = change.get("address", f"unknown-{idx}")
            actions = change.get("change", {}).get("actions", [])
            category = "security" if any(x in address.lower() for x in ["security_group", "iam", "policy"]) else "terraform"
            severity = "P1" if category == "security" else "P2"
            findings.append(Finding(
                id=f"tf-drift-{idx}",
                title=f"Terraform drift detected: {address}",
                category="terraform",
                severity=severity,
                evidence=[Evidence(
                    source="terraform_plan",
                    path=address,
                    observed=",".join(actions),
                    expected="no-op",
                    collector=self.name,
                )],
                impact={
                    "user_impact": "Runtime behavior may differ from expected service baseline.",
                    "business_impact": "Compliance, cost, or audit posture may be affected.",
                    "technical_impact": "Declared Terraform state and cloud resource state differ.",
                },
                recommendation={
                    "summary": "Review drift, determine whether to import, revert, or update Terraform, then open an approval-gated PR.",
                    "remediation_type": "approval_required",
                },
                confidence={"score": 0.88, "explanation": "Terraform plan contains resource actions indicating drift or pending change."},
            ))

        numeric = max(0, 100 - len(findings) * 15)
        grade = "A" if numeric >= 90 else "B" if numeric >= 75 else "C" if numeric >= 60 else "D" if numeric >= 45 else "F"
        return {
            "environment": environment,
            "status": "drift_detected" if findings else "no_drift",
            "severity": "P1" if any(f.severity == "P1" for f in findings) else ("P2" if findings else "INFO"),
            "score": Score(
                name="terraform_drift",
                grade=grade,
                numeric_score=numeric,
                rationale="Terraform drift score from non-noop plan actions.",
                blockers=[f.id for f in findings if f.severity in ("P0", "P1")],
            ).to_dict(),
            "findings": [f.to_dict() for f in findings],
        }
