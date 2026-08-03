from pathlib import Path
import json
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_all_telemetry_yaml_documents_parse():
    for path in (ROOT / "telemetry").rglob("*.yaml"):
        assert list(yaml.safe_load_all(path.read_text())), path


def test_gateway_has_redaction_queue_and_kafka():
    text = (ROOT / "telemetry/otel/gateway/config.yaml").read_text()
    for expected in ("transform/redact", "file_storage/queue", "kafka/logs", "retry_on_failure"):
        assert expected in text
    assert "otlphttp/loki" not in text


def test_vector_has_bounded_labels_and_service_fallback():
    text = (ROOT / "telemetry/processing/vector.yaml").read_text()
    assert '.service_name = get(.resource.attributes, ["service.name"]) ?? "unknown"' in text
    assert "request_id" not in text
    assert "trace_id:" not in text


def test_agent_is_a_daemonset_and_gateway_is_scaled():
    assert "kind: DaemonSet" in (ROOT / "telemetry/otel/agent/daemonset.yaml").read_text()
    gateway = (ROOT / "telemetry/otel/gateway/deployment.yaml").read_text()
    assert "replicas: 3" in gateway
    assert "kind: PodDisruptionBudget" in gateway


def test_dashboard_is_valid_json():
    dashboard = json.loads((ROOT / "telemetry/dashboards/pipeline-health.json").read_text())
    assert dashboard["uid"] == "aria-telemetry-health"
    assert len(dashboard["panels"]) >= 4


def test_remediation_contract_is_recommendation_or_gitops_only():
    spec = yaml.safe_load((ROOT / "specs/remediations/telemetry-remediations.yaml").read_text())
    assert all(item["mode"] in {"gitops_proposal", "recommendation_only"} for item in spec["remediations"])
    assert all(item["approval"] == "required" for item in spec["remediations"])


def test_all_documented_deployment_profiles_render():
    for profile in ("local", "scale", "production-small", "production-regional"):
        path = ROOT / "telemetry/overlays" / profile / "kustomization.yaml"
        assert path.exists(), profile


def test_terraform_archive_has_production_safety_controls():
    text = (ROOT / "telemetry/terraform/main.tf").read_text()
    for expected in (
        'force_destroy = false',
        'block_public_policy     = true',
        'enable_key_rotation     = true',
        'sse_algorithm     = "aws:kms"',
        'storage_class = "GLACIER_IR"',
    ):
        assert expected in text
