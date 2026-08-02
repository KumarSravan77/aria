from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from server.platform.service_review.agent import AIServiceReviewAgent


@dataclass
class HarnessResult:
    scenario: str
    passed: bool
    failures: List[str]
    report: Dict[str, Any]


class SpecHarness:
    """Small deterministic harness for spec-driven ARIA development."""

    def run_service_review_scenario(self, scenario: Dict[str, Any], fixtures: Dict[str, Any]) -> HarnessResult:
        agent = AIServiceReviewAgent()
        scenario_meta = scenario["scenario"]
        report = agent.review(
            service_id=scenario_meta["service_id"],
            environment=scenario_meta["environment"],
            service_profile=fixtures["service_profile"],
            slo_config=fixtures.get("slo_config"),
            telemetry_snapshot=fixtures.get("telemetry_snapshot"),
            incident_history=fixtures.get("incident_history"),
            latest_drift_summary=fixtures.get("latest_drift_summary"),
        ).to_dict()

        failures: List[str] = []
        expected = scenario.get("expected", {})
        findings = report["findings"]

        for required in expected.get("findings", {}).get("must_include", []):
            if not any(
                f.get("category") == required.get("category")
                and f.get("severity") == required.get("severity")
                and required.get("title_contains", "") in f.get("title", "")
                for f in findings
            ):
                failures.append(f"Missing expected finding: {required}")

        for forbidden in expected.get("findings", {}).get("must_not_include", []):
            if any(
                f.get("category") == forbidden.get("category")
                and forbidden.get("title_contains", "") in f.get("title", "")
                for f in findings
            ):
                failures.append(f"Found forbidden finding: {forbidden}")

        if "terraform-drift-agent" not in report["agents_not_run"]:
            failures.append("Service review must not execute terraform-drift-agent")

        if expected.get("approval_expectations", {}).get("approval_required") and not report["approval_required_actions"]:
            failures.append("Expected approval_required_actions to be non-empty")

        return HarnessResult(
            scenario=scenario_meta["name"],
            passed=not failures,
            failures=failures,
            report=report,
        )
