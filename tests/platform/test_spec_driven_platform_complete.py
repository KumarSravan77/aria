from pathlib import Path

import yaml

from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader

ROOT = Path(__file__).resolve().parents[2]


def test_spec_index_loads_all_core_sections():
    loader = SpecLoader(ROOT)
    index = loader.load_index()["spec_index"]
    for section in ["capabilities", "golden_paths", "policies", "decisions", "remediations", "workflows"]:
        assert section in index
        assert index[section], f"{section} should not be empty"


def test_payments_api_resolves_java_tier1_golden_path():
    loader = SpecLoader(ROOT)
    profile = loader.load_service_profile("payments-api")
    assert profile["service"]["golden_path"] == "java-springboot-tier1"
    golden_path = loader.load_golden_path("java-springboot-tier1")
    assert "kubernetes-standards" in golden_path["required_capabilities"]


def test_spec_driven_evaluator_passes_when_capabilities_exist():
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service("payments-api")
    data = result.to_dict()
    assert data["passed"] is True
    assert data["missing_capabilities"] == []
    assert "kubernetes-standards" in data["satisfied_capabilities"]
    assert data["production_gates"]["require_approval"] is True


def test_governance_specs_load_decisions_and_remediations():
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service("payments-api")
    assert result.decision_rules_loaded >= 3
    assert result.remediation_specs_loaded >= 3


def test_spec_validation_workflow_exists():
    workflow = ROOT / ".github" / "workflows" / "spec-validation.yml"
    assert workflow.exists()
    parsed = yaml.safe_load(workflow.read_text())
    assert parsed["jobs"]["validate-specs"]
