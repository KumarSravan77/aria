from server.platform.onboarding.agent import OnboardingAgent
from server.platform.service_review.agent import AIServiceReviewAgent
from server.platform.spec_harness.runner import SpecHarness
from server.platform.terraform_drift.agent import TerraformDriftAgent


def test_service_review_detects_slo_and_error_budget_breach_without_running_drift():
    agent = AIServiceReviewAgent()
    report = agent.review(
        service_id="payments-api",
        environment="prod",
        service_profile={
            "kubernetes": {"readinessProbe": True, "livenessProbe": True, "pdb": True},
            "observability": {"otel_enabled": True},
            "cicd": {"rollback": True},
        },
        slo_config={"availability_target_percent": 99.95, "latency_p95_ms": 300},
        telemetry_snapshot={
            "availability_percent": 99.89,
            "error_budget_remaining_percent": 4,
            "burn_rate": 6.5,
            "latency_p95_ms": 420,
        },
    ).to_dict()

    assert "terraform-drift-agent" in report["agents_not_run"]
    assert any(f["category"] == "reliability" and "SLO breached" in f["title"] for f in report["findings"])
    assert any("Error budget" in f["title"] for f in report["findings"])
    assert report["approval_required_actions"]


def test_service_review_consumes_existing_drift_summary_but_does_not_run_drift():
    agent = AIServiceReviewAgent()
    report = agent.review(
        service_id="payments-api",
        environment="prod",
        service_profile={
            "kubernetes": {"readinessProbe": True, "livenessProbe": True, "pdb": True},
            "observability": {"otel_enabled": True},
            "cicd": {"rollback": True},
        },
        latest_drift_summary={"status": "drift_detected", "severity": "P2"},
    ).to_dict()

    assert report["consumed_inputs"]["latest_drift_summary"] is True
    assert "terraform-drift-agent" in report["agents_not_run"]
    assert any(f["id"] == "tf-drift-summary-risk" for f in report["findings"])


def test_terraform_drift_agent_is_independent():
    result = TerraformDriftAgent().analyze(
        terraform_plan={
            "resource_changes": [
                {
                    "address": "aws_security_group.app",
                    "change": {"actions": ["update"]},
                }
            ]
        },
        environment="prod",
    )

    assert result["status"] == "drift_detected"
    assert result["severity"] == "P1"
    assert result["findings"][0]["category"] == "terraform"


def test_onboarding_agent_runs_drift_baseline_and_service_review():
    result = OnboardingAgent().onboard(
        service_id="payments-api",
        environment="prod",
        service_profile={
            "kubernetes": {"readinessProbe": False, "livenessProbe": False, "pdb": False},
            "observability": {"otel_enabled": False},
            "cicd": {"rollback": False},
        },
        terraform_plan={"resource_changes": []},
    )

    assert result["baseline"]["terraform_drift"]["status"] == "no_drift"
    assert result["baseline"]["service_review"]["findings"]
    assert "kubernetes/helm-values.yaml" in result["generated_platform_templates"]


def test_harness_validates_golden_slo_breach_scenario():
    scenario = {
        "scenario": {"name": "tier1-service-slo-breach", "service_id": "payments-api", "environment": "prod"},
        "expected": {
            "findings": {
                "must_include": [
                    {"category": "reliability", "severity": "P1", "title_contains": "SLO breached"},
                    {"category": "reliability", "severity": "P1", "title_contains": "Error budget"},
                ],
                "must_not_include": [
                    {"category": "terraform", "title_contains": "Run drift scan"},
                ],
            },
            "approval_expectations": {"approval_required": True},
        },
    }
    fixtures = {
        "service_profile": {
            "kubernetes": {"readinessProbe": True, "livenessProbe": True, "pdb": True},
            "observability": {"otel_enabled": True},
            "cicd": {"rollback": True},
        },
        "slo_config": {"availability_target_percent": 99.95, "latency_p95_ms": 300},
        "telemetry_snapshot": {
            "availability_percent": 99.89,
            "error_budget_remaining_percent": 4,
            "burn_rate": 6.5,
            "latency_p95_ms": 420,
        },
        "latest_drift_summary": {"status": "no_drift", "severity": "INFO"},
    }

    result = SpecHarness().run_service_review_scenario(scenario, fixtures)
    assert result.passed, result.failures
