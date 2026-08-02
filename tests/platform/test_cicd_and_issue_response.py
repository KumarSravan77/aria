from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.cicd_pipeline import CICDPipelineGenerator
from server.platform.issue_response import AIIssueResponseAgent


def test_cicd_pipeline_generator_creates_golden_path_github_actions():
    generator = CICDPipelineGenerator()
    template = generator.generate({
        "service_id": "payments-api",
        "language": "java",
        "cicd": {"provider": "github-actions"},
        "deployment": {"target": "kubernetes"},
    }).to_dict()

    assert template["service_id"] == "payments-api"
    assert template["provider"] == "github-actions"
    stage_names = [stage["name"] for stage in template["stages"]]
    assert "security" in stage_names
    assert "slo_check" in stage_names
    assert "post_deploy_ai_review" in stage_names
    assert ".github/workflows/aria-golden-path.yml" in template["generated_files"]


def test_control_plane_exposes_cicd_generation():
    cp = ARIAPlatformControlPlane()
    result = cp.generate_cicd_pipeline({
        "service_id": "checkout-api",
        "language": "python",
        "cicd_provider": "jenkins",
        "deployment_target": "kubernetes",
    })

    assert result["provider"] == "jenkins"
    assert "Jenkinsfile" in result["generated_files"]
    assert "required_gates" in result["standards"]


def test_issue_response_agent_handles_pipeline_failure():
    agent = AIIssueResponseAgent()
    plan = agent.analyze({
        "event_type": "pipeline_failure",
        "service_id": "payments-api",
        "environment": "stage",
        "severity": "P2",
        "source": "github-actions",
        "signals": {"failed_stage": "security"},
        "context": {
            "service_profile": {
                "service_id": "payments-api",
                "cicd": {"build": True, "unit_tests": True, "rollback": True},
                "kubernetes": {"readinessProbe": True, "livenessProbe": True, "pdb": True},
                "observability": {"otel_enabled": True},
            }
        },
    })

    assert plan["incident_mode"] == "release_guard"
    assert "cicd-standards-agent" in plan["agents_to_run"]
    assert any(action["type"] == "block_promotion" for action in plan["recommended_actions"])
    assert plan["service_review"]["service_id"] == "payments-api"


def test_issue_response_agent_handles_slo_burn_with_rollback_guard():
    cp = ARIAPlatformControlPlane()
    plan = cp.handle_issue_event({
        "event_type": "slo_burn",
        "service_id": "checkout-api",
        "environment": "prod",
        "severity": "P1",
        "signals": {"post_deploy_slo_burn": True, "error_budget_remaining_percent": 2.0},
        "context": {
            "service_profile": {
                "service_id": "checkout-api",
                "kubernetes": {"readinessProbe": True, "livenessProbe": True},
                "observability": {"otel_enabled": True},
                "cicd": {"build": True, "unit_tests": True, "security_scan": True, "rollback": True, "deployment_strategy": True},
            },
            "slo_config": {"availability_target": 99.9, "latency_p95_target_ms": 500, "error_rate_target": 0.01},
            "telemetry_snapshot": {"availability": 99.1, "latency_p95_ms": 900, "error_rate": 0.03, "error_budget_remaining_percent": 2.0, "burn_rate": 7.5},
        },
    })

    assert plan["incident_mode"] == "active_incident"
    assert plan["approval_required"] is True
    assert plan["rollback_recommended"] is True
    assert "reliability-agent" in plan["agents_to_run"]
    assert plan["service_review"]["consumed_inputs"]["slo_config"] is True
