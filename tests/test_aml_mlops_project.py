from __future__ import annotations

import json
from pathlib import Path

import yaml

from server.domain.scenario_catalog import list_scenarios
from server.platform.control_plane import ARIAPlatformControlPlane
from server.platform.spec_engine import SpecDrivenEvaluator, SpecLoader

ROOT = Path(__file__).resolve().parents[1]


def test_aml_golden_path_loaded():
    index = SpecLoader(ROOT).load_index()["spec_index"]
    assert "specs/golden-paths/python-aml-mlops.yaml" in index["golden_paths"]


def test_data_pipeline_capability_loaded():
    caps = SpecLoader(ROOT).load_collection("capabilities")
    assert any(c.get("capability", {}).get("name") == "data-pipeline-standards" for c in caps)


def test_model_governance_capability_loaded():
    caps = SpecLoader(ROOT).load_collection("capabilities")
    assert any(c.get("capability", {}).get("name") == "model-governance" for c in caps)


def test_aml_feature_pipeline_service_profile_evaluates():
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service("aml-feature-pipeline")
    assert result.golden_path == "python-aml-mlops"
    assert "data-pipeline-standards" in result.satisfied_capabilities
    assert "model-governance" in result.satisfied_capabilities
    assert result.passed is True


def test_mlops_golden_path_auto_selected():
    cp = ARIAPlatformControlPlane()
    assert cp._default_golden_path({"workload_type": "mlops", "language": "python"}) == "python-aml-mlops"


def test_fraud_detection_engine_profile_evaluates():
    result = SpecDrivenEvaluator(SpecLoader(ROOT)).evaluate_service("fraud-detection-engine")
    assert result.golden_path == "java-springboot-tier1"
    assert result.passed is True


def test_aml_model_drift_scenario_in_catalog():
    scenarios = list_scenarios("aml_fraud")
    assert any(s["id"] == "aml-model-drift" for s in scenarios)


def test_aml_dataset_loads():
    data = json.loads((ROOT / "datasets/aml-fraud/sample_transactions.json").read_text())
    required = {"transaction_id", "amount", "currency", "sender_country", "receiver_country", "transaction_type", "velocity_1h", "is_fraud_label", "model_score", "explanation_top_features"}
    assert data
    assert required.issubset(data[0].keys())


def test_model_drift_dataset_has_scenarios():
    data = json.loads((ROOT / "datasets/aml-fraud/model_drift_scenarios.json").read_text())
    assert len(data) == 3
    assert all("safe_remediation" in item for item in data)


def test_canadian_enterprise_registry_has_aml_feature_pipeline():
    registry = yaml.safe_load((ROOT / "config/canadian_enterprise_services.yaml").read_text())
    services = registry["domains"]["aml_fraud"]["services"]
    assert any(s["name"] == "aml-feature-pipeline" for s in services)
