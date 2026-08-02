from pathlib import Path

import yaml

from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str):
    return yaml.safe_load((ROOT / path).read_text())


def test_service_mesh_and_gitops_specs_registered():
    index = load_yaml("specs/platform/spec-index.yaml")["spec_index"]
    assert "specs/capabilities/service-mesh-standards.yaml" in index["capabilities"]
    assert "specs/capabilities/gitops-standards.yaml" in index["capabilities"]


def test_aml_golden_path_requires_standard_architecture_capabilities():
    spec = load_yaml("specs/golden-paths/python-aml-mlops.yaml")
    required = spec.get("required_capabilities", [])
    assert "service-mesh-standards" in required
    assert "gitops-standards" in required
    assert "cicd-standards" in required
    assert "observability-standards" in required
    assert "data-pipeline-standards" in required
    assert "model-governance" in required


def test_aml_profiles_declare_istio_and_argocd():
    for service_id in ["aml-feature-pipeline", "fraud-detection-engine"]:
        profile = load_yaml(f"specs/service-profiles/{service_id}.yaml")["service"]
        assert profile["mesh"] == "istio"
        assert profile["gitops"] == "argocd"
        assert profile["delivery"]["ci"] == "github-actions"
        assert profile["delivery"]["cd"] == "argocd"
        assert profile["observability"]["otel"] is True


def test_aml_service_evaluates_with_new_capabilities_satisfied():
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service("aml-feature-pipeline")
    data = result.to_dict()
    assert data["golden_path"] == "python-aml-mlops"
    assert "service-mesh-standards" in data["satisfied_capabilities"]
    assert "gitops-standards" in data["satisfied_capabilities"]
    assert data["passed"] is True


def test_istio_and_argocd_reference_manifests_exist():
    assert (ROOT / "platform/aml-mlops/istio/aml-inference-traffic.yaml").exists()
    assert (ROOT / "platform/aml-mlops/argocd/aml-feature-pipeline-app.yaml").exists()
