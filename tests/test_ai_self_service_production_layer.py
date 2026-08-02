import json
from pathlib import Path

from server.platform.connectors.git_repo import GitRepoConnector
from server.platform.connectors.kubernetes import KubernetesConnector
from server.platform.connectors.telemetry import TelemetryConnector
from server.platform.reports.markdown import MarkdownServiceReviewReport
from server.platform.terraform_drift.executor import TerraformPlanExecutor
from server.platform.workflows.self_service import SelfServiceDevOpsWorkflow


def test_git_repo_connector_detects_platform_signals(tmp_path: Path):
    (tmp_path / "pom.xml").write_text("<project />")
    (tmp_path / "Jenkinsfile").write_text("pipeline {}")
    (tmp_path / "main.tf").write_text("resource \"aws_s3_bucket\" \"x\" {}")
    k8s = tmp_path / "k8s"
    k8s.mkdir()
    (k8s / "deployment.yaml").write_text("kind: Deployment")

    scan = GitRepoConnector().scan(str(tmp_path))

    assert scan["language"] == "java"
    assert scan["ci_cd"]
    assert scan["terraform"]
    assert scan["kubernetes"]


def test_kubernetes_connector_normalizes_probe_and_resource_standards():
    resources = [{
        "kind": "Deployment",
        "spec": {"template": {"spec": {"containers": [{
            "name": "api",
            "livenessProbe": {"httpGet": {"path": "/live"}},
            "readinessProbe": {"httpGet": {"path": "/ready"}},
            "resources": {"requests": {"cpu": "250m", "memory": "512Mi"}}
        }]}}}
    }, {"kind": "HorizontalPodAutoscaler"}]

    normalized = KubernetesConnector().normalize_resources(resources)

    assert normalized["has_deployment"] is True
    assert normalized["has_hpa"] is True
    assert normalized["probes_configured"] is True
    assert normalized["resources_configured"] is True


def test_terraform_executor_parses_json_plan(tmp_path: Path):
    plan = {"resource_changes": [{"address": "aws_security_group.api", "change": {"actions": ["update"]}}]}
    path = tmp_path / "tfplan.json"
    path.write_text(json.dumps(plan))

    parsed = TerraformPlanExecutor().parse_plan_json(str(path))

    assert parsed["resource_changes"][0]["address"] == "aws_security_group.api"


def test_self_service_workflow_generates_report_and_approvals(tmp_path: Path):
    workflow = SelfServiceDevOpsWorkflow()
    context = workflow.build_context(
        service_id="payments-api",
        environment="prod",
        service_profile={"tier": "tier1", "language": "java"},
        telemetry_metrics={
            "availability": 99.80,
            "latency_p95_ms": 800,
            "error_rate_percent": 1.2,
            "error_budget_remaining_percent": 2,
            "burn_rate": 8.0,
        },
        pipeline={"provider": "jenkins", "stages": ["build", "unit_tests", "sbom", "deploy"]},
    )

    result = workflow.onboard_and_review(context, output_dir=str(tmp_path))

    assert result["service_review"]["service_id"] == "payments-api"
    assert "ARIA Service Review Report" in result["markdown_report"]
    assert result["written_report"]
    assert result["approval_requests"]


def test_markdown_report_contains_scores_and_findings():
    review = {
        "service_id": "svc",
        "environment": "dev",
        "executive_summary": "summary",
        "scores": {"reliability": {"grade": "B", "numeric_score": 80, "rationale": "ok"}},
        "findings": [{"severity": "P2", "category": "kubernetes", "title": "Missing PDB", "recommendation": {"summary": "Add PDB"}}],
        "approval_required_actions": [],
        "agents_run": ["reliability-agent"],
        "agents_not_run": ["terraform-drift-agent"],
    }

    md = MarkdownServiceReviewReport().render(review)

    assert "## Scores" in md
    assert "Missing PDB" in md
    assert "terraform-drift-agent" in md
