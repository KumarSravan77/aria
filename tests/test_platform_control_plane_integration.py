from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.onboarding.templates import PlatformTemplateGenerator
from server.platform.service_review.agent import AIServiceReviewAgent


def _complete_profile():
    return {
        "service_id": "orders-api",
        "language": "java",
        "framework": "spring-boot",
        "tier": "tier1",
        "kubernetes": {
            "readinessProbe": True,
            "livenessProbe": True,
            "startupProbe": True,
            "pdb": True,
            "resources": {"requests": {"cpu": "250m", "memory": "512Mi"}, "limits": {"cpu": "1", "memory": "1Gi"}},
            "topologySpreadConstraints": True,
        },
        "observability": {
            "otel_enabled": True,
            "metrics": True,
            "logs": True,
            "traces": True,
            "dashboards": True,
            "alerts": True,
            "correlation_id": True,
            "otel": {"service_name": "orders-api", "trace_context_propagation": True, "collector": True, "high_cardinality_attributes": []},
        },
        "cicd": {"build": True, "unit_tests": True, "security_scan": True, "sbom": True, "artifact_signing": True, "rollback": True, "deployment_strategy": "canary"},
        "security": {"rbac_least_privilege": True, "network_policy": True, "pod_security_context": True, "secret_management": True, "image_scan": True, "policy_as_code": True},
        "cost": {"owner_tag": "team-platform", "budget_alerts": True, "monthly_spend_usd": 1000},
        "runbook": {"owner": "team-platform", "escalation": "pagerduty", "dashboards": ["dynatrace"], "rollback_steps": "pipeline rollback", "known_failure_modes": ["5xx"]},
    }


def test_service_review_runs_specialist_agents_and_produces_scores():
    report = AIServiceReviewAgent().review(
        service_id="orders-api",
        environment="prod",
        service_profile=_complete_profile(),
        slo_config={"availability_target_percent": 99.9, "latency_p95_ms": 300},
        telemetry_snapshot={"availability_percent": 99.95, "error_budget_remaining_percent": 80, "burn_rate": 0.5, "latency_p95_ms": 180},
    ).to_dict()

    for score in ["kubernetes", "observability", "otel_guardian", "cicd", "security", "cost", "runbook", "reliability", "operational_readiness"]:
        assert score in report["scores"]
    assert "terraform-drift-agent" in report["agents_not_run"]
    assert not report["approval_required_actions"]


def test_platform_control_plane_supports_self_service_onboarding_and_drift():
    cp = ARIAPlatformControlPlane()
    onboarding = cp.onboard_service({
        "service_id": "orders-api",
        "environment": "dev",
        "service_profile": _complete_profile(),
        "terraform_plan": {"resource_changes": []},
    })
    assert "generated_artifacts" in onboarding
    assert "kubernetes/helm-values.yaml" in onboarding["generated_artifacts"]
    drift = cp.run_terraform_drift({"resource_changes": [{"address": "aws_iam_policy.app", "change": {"actions": ["update"]}}]}, "prod")
    assert drift["status"] == "drift_detected"
    assert drift["severity"] == "P1"


def test_template_generator_outputs_golden_path_artifacts():
    artifacts = PlatformTemplateGenerator().generate("orders-api", {"language": "java", "tier": "tier1"})
    assert "OTEL" not in artifacts["observability/otel-collector.yaml"]  # human-readable collector template, not env dump
    assert "rollback_guard" in artifacts["cicd/pipeline-template.yaml"]
    assert "availability" in artifacts["slo/service-slo.yaml"]
