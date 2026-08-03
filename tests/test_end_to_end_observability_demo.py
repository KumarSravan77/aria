from pathlib import Path
import json
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_demo_services_emit_and_propagate_trace_context():
    checkout = (ROOT / "apps/sample-checkout-api/app.py").read_text()
    inventory = (ROOT / "apps/inventory-api/app.py").read_text()
    assert "RequestsInstrumentor().instrument()" in checkout
    assert "inventory-api" in checkout
    for source in (checkout, inventory):
        assert '"trace_id"' in source
        assert '"span_id"' in source
        assert "OTLPSpanExporter" in source
        assert "exemplar" in source
        assert "prometheus_client.openmetrics.exposition" in source


def test_gateway_generates_span_metrics_and_routes_all_signals():
    manifest = yaml.safe_load((ROOT / "telemetry/otel/gateway/config.yaml").read_text())
    config = yaml.safe_load(manifest["data"]["collector.yaml"])
    assert "spanmetrics" in config["connectors"]
    assert "spanmetrics" in config["service"]["pipelines"]["traces"]["exporters"]
    assert "spanmetrics" in config["service"]["pipelines"]["metrics"]["receivers"]
    assert config["service"]["pipelines"]["logs"]["exporters"] == ["kafka/logs"]


def test_grafana_has_trace_log_metric_correlation():
    values = yaml.safe_load((ROOT / "k8s/monitoring/prometheus-values.yaml").read_text())
    sources = {source["uid"]: source for source in values["grafana"]["additionalDataSources"]}
    assert sources["loki"]["jsonData"]["derivedFields"][0]["datasourceUid"] == "tempo"
    assert sources["tempo"]["jsonData"]["tracesToLogsV2"]["datasourceUid"] == "loki"
    assert sources["tempo"]["jsonData"]["tracesToMetrics"]["datasourceUid"] == "prometheus"
    assert "exemplar-storage" in values["prometheus"]["prometheusSpec"]["enableFeatures"]


def test_application_dashboard_and_verifier_exist():
    dashboard = json.loads((ROOT / "telemetry/dashboards/application-overview.json").read_text())
    types = {panel["type"] for panel in dashboard["panels"]}
    assert {"stat", "timeseries", "logs", "traces"}.issubset(types)
    verifier = (ROOT / "scripts/verify_e2e_observability.py").read_text()
    assert all(path in verifier for path in ("/api/v1/query", "/loki/api/v1/query_range", "/api/traces/"))


def test_demo_kubernetes_manifests_parse():
    for name in ("sample-checkout-api.yaml", "inventory-api.yaml", "banking-demo.yaml"):
        assert list(yaml.safe_load_all((ROOT / "k8s/apps" / name).read_text()))


def test_featured_banking_demo_is_fictional_and_correlated():
    services = ("banking-api", "fraud-detection-api", "transaction-ledger-api")
    for service in services:
        source = (ROOT / "apps" / service / "app.py").read_text()
        assert "OTLPSpanExporter" in source
        assert '"trace_id"' in source
        assert '"span_id"' in source
        assert "mapletrust-bank" in source
    banking = (ROOT / "apps/banking-api/app.py").read_text()
    assert "RequestsInstrumentor().instrument()" in banking
    assert "fraud-detection-api" in banking
    assert "transaction-ledger-api" in banking
    docs = (ROOT / "docs/END_TO_END_OBSERVABILITY_DEMO.md").read_text()
    assert "fictional Canadian" in docs
    assert "not affiliated with CIBC, RBC" in docs
