from server.chaos.experiment_catalog import get_experiment, list_experiments
from server.chaos.litmus_client import LitmusChaosClient
from server.chaos.validation_engine import ChaosValidationEngine
from server.chaos.chaos_reporter import ChaosReporter


def test_chaos_catalog_contains_core_experiments():
    names = {item["name"] for item in list_experiments()}
    assert {"pod-delete", "cpu-hog", "memory-hog", "network-latency", "dns-failure"}.issubset(names)
    assert get_experiment("pod-delete").litmus_experiment == "pod-delete"


def test_litmus_client_dry_run_generates_manifest_without_kubernetes():
    client = LitmusChaosClient()
    result = client.run_experiment(
        experiment="pod-delete",
        namespace="demo",
        service="checkout-api",
        app_label="app=checkout-api",
        dry_run=True,
    )
    assert result["executed"] is False
    assert result["dry_run"] is True
    assert result["manifest"]["kind"] == "ChaosEngine"
    assert result["manifest"]["spec"]["appinfo"]["applabel"] == "app=checkout-api"


def test_resilience_validation_scores_successful_experiment():
    validation = ChaosValidationEngine().validate(
        service="checkout-api",
        experiment="pod-delete",
        incident_created=True,
        alert_fired=True,
        healing_succeeded=True,
        rag_sources=5,
        mttr_seconds=42,
        slo_burn_observed=True,
    )
    assert validation["status"] == "passed"
    assert validation["resilience_score"] >= 90


def test_chaos_report_contains_score_and_checks():
    validation = ChaosValidationEngine().validate(
        service="checkout-api",
        experiment="cpu-hog",
        incident_created=True,
        alert_fired=False,
        healing_succeeded=False,
        rag_sources=0,
        mttr_seconds=400,
        slo_burn_observed=True,
    )
    markdown = ChaosReporter().markdown(validation)
    assert "Chaos Resilience Report" in markdown
    assert "Resilience score" in markdown
    assert "alerting" in markdown.lower() or "alert" in markdown.lower()
