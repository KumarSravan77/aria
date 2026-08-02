from server.platform.secrets import SecretBroker, SecretGovernanceAgent, SecretRedactor
from server.platform.secrets.broker import SecretRequest


def test_secret_redactor_removes_common_patterns():
    result = SecretRedactor().redact_text("token: ghp_abcdefghijklmnopqrstuvwxyz123456 password=supersecret")
    assert "ghp_" not in result.text
    assert "supersecret" not in result.text
    assert result.redactions


def test_secret_broker_returns_lease_not_raw_secret():
    response = SecretBroker().request_secret_lease(SecretRequest(
        service_id="payments-api",
        environment="prod",
        secret_ref="kv/payments-api/database",
        purpose="runtime",
    ))
    assert response["status"] == "lease_issued"
    assert response["raw_secret_returned"] is False
    assert response["lease"]["provider"] == "vault"


def test_secret_governance_detects_ci_static_secret_and_sanitizes():
    payload = {
        "service_id": "payments-api",
        "workflow": "env: TOKEN=${{ secrets.PROD_TOKEN }}",
        "logs": "api_key: abcdefghijklmnop",
    }
    review = SecretGovernanceAgent().review(payload)
    assert review["score"] in {"B", "C"}
    assert any(f["category"] in {"secrets", "cicd"} for f in review["findings"])
    assert "abcdefghijklmnop" not in review["sanitized_preview"]


def test_sanitize_for_rag_never_retains_raw_secret():
    doc = {"body": "password: topsecret12345", "team": "platform"}
    output = SecretGovernanceAgent().sanitize_for_rag(doc)
    assert output["raw_secret_retained"] is False
    assert "topsecret12345" not in str(output)
