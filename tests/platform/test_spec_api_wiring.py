from server.platform.api.router import evaluate_service_specs as api_evaluate_specs


def test_spec_api_evaluate_returns_passed_result():
    result = api_evaluate_specs({"service_id": "payments-api"})
    assert result["service_id"] == "payments-api"
    assert result["passed"] is True
    assert "kubernetes-standards" in result["satisfied_capabilities"]
