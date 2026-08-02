from server.domain.service_registry import ServiceRegistry
from server.domain.scenario_catalog import list_scenarios


def test_domains_are_loaded():
    domains = ServiceRegistry().list_domains()
    names = {d["domain"] for d in domains}
    assert "capital_markets" in names
    assert "retail_banking" in names
    assert "wealth_management" in names
    assert "aml_fraud" in names
    assert "insurance" in names
    assert "retail_ecommerce" in names


def test_payment_service_context():
    ctx = ServiceRegistry().incident_context("payment-processing-api")
    assert ctx["found"] is True
    assert ctx["domain"] == "retail_banking"
    assert ctx["owner_team"] == "payments-platform"


def test_scenarios_exist_for_all_domains():
    scenarios = list_scenarios()
    domains = {s["domain"] for s in scenarios}
    assert "capital_markets" in domains
    assert "aml_fraud" in domains
    assert "retail_ecommerce" in domains
