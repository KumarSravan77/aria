from pathlib import Path

from fastapi.testclient import TestClient

from server.api.main import app
from server.config import settings
from server.platform.control_plane import ARIAPlatformControlPlane


def auth_headers():
    return {"Authorization": f"Bearer {settings.api_auth_token}"}


def test_platform_routes_require_auth():
    client = TestClient(app)
    response = client.post("/platform/self-service/specs/evaluate", json={"service_id": "payments-api"})
    assert response.status_code in {401, 403}


def test_specs_evaluate_uses_requested_service_id():
    client = TestClient(app)
    response = client.post(
        "/platform/self-service/specs/evaluate",
        json={"service_id": "payments-api"},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["service_id"] == "payments-api"


def test_missing_cicd_and_issue_routes_are_wired():
    client = TestClient(app)
    cicd = client.post(
        "/platform/self-service/cicd/generate",
        json={"service_id": "payments-api", "language": "java", "cicd_provider": "github-actions"},
        headers=auth_headers(),
    )
    assert cicd.status_code == 200
    assert ".github/workflows/aria-golden-path.yml" in cicd.json()["generated_files"]

    issue = client.post(
        "/platform/self-service/issue-event",
        json={"service_id": "payments-api", "event_type": "pipeline_failure", "logs": "mvn test failed"},
        headers=auth_headers(),
    )
    assert issue.status_code == 200
    assert issue.json()["event_type"] == "pipeline_failure"
    assert issue.json()["agents_to_run"]


def test_onboarding_creates_service_profile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("specs/service-profiles").mkdir(parents=True)
    cp = ARIAPlatformControlPlane()
    result = cp.onboard_service({
        "service_id": "orders-api",
        "environment": "dev",
        "service_profile": {
            "language": "java",
            "framework": "spring-boot",
            "tier": "tier1",
            "team": "platform",
        },
    })
    profile_path = tmp_path / "specs/service-profiles/orders-api.yaml"
    assert profile_path.exists()
    assert result["service_profile_spec"]["created"] is True


def test_cicd_generator_can_write_real_workflow_file(tmp_path):
    cp = ARIAPlatformControlPlane()
    result = cp.generate_cicd_pipeline({
        "service_id": "payments-api",
        "language": "java",
        "cicd_provider": "github-actions",
        "write_files": True,
        "output_dir": str(tmp_path),
    })
    workflow = tmp_path / ".github/workflows/aria-golden-path.yml"
    assert workflow.exists()
    assert "ARIA Golden Path CI/CD" in workflow.read_text()
    assert str(workflow) in result["written_files"]
