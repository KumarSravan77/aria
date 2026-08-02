from __future__ import annotations

import pytest
from server.platform.secrets.redaction import SecretRedactor
from server.platform.secrets.broker import SecretBroker, SecretRequest
from server.platform.secrets.governance import SecretGovernanceAgent


# ── SecretRedactor ────────────────────────────────────────────────────────────

class TestSecretRedactor:
    def setup_method(self):
        self.r = SecretRedactor()

    def test_redacts_aws_access_key(self):
        # Exactly AKIA + 16 uppercase/digit chars, terminated by a space (word boundary)
        text = "key=AKIAIOSFODNN7EXAMPLE here"
        result = self.r.redact_text(text)
        assert "AKIA" not in result.text
        assert any(r["type"] == "aws_access_key" for r in result.redactions)

    def test_redacts_github_token(self):
        # Standalone token (no "token:" prefix) so generic_api_key doesn't re-match
        text = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabc123"
        result = self.r.redact_text(text)
        assert "ghp_" not in result.text
        assert any(r["type"] == "github_token" for r in result.redactions)

    def test_redacts_generic_api_key(self):
        text = "api_key=supersecretvalue123"
        result = self.r.redact_text(text)
        assert "supersecretvalue123" not in result.text

    def test_redacts_connection_string_password(self):
        text = "postgres://user:password=hunter2;host=db"
        result = self.r.redact_text(text)
        assert "hunter2" not in result.text

    def test_clean_text_has_no_redactions(self):
        result = self.r.redact_text("service: checkout-api env: dev")
        assert result.redactions == []
        assert result.text == "service: checkout-api env: dev"

    def test_none_input_returns_empty_string(self):
        result = self.r.redact_text(None)
        assert result.text == ""
        assert result.redactions == []

    def test_redact_payload_sanitizes_sensitive_key_names(self):
        payload = {"service_id": "api", "password": "hunter2", "api_key": "abc123"}
        sanitized = self.r.redact_payload(payload)
        assert sanitized["service_id"] == "api"
        assert sanitized["password"] == "[REDACTED:key-name]"
        assert sanitized["api_key"] == "[REDACTED:key-name]"

    def test_redact_payload_handles_nested_dict(self):
        payload = {"db": {"password": "s3cr3t", "host": "localhost"}}
        sanitized = self.r.redact_payload(payload)
        assert sanitized["db"]["password"] == "[REDACTED:key-name]"
        assert sanitized["db"]["host"] == "localhost"

    def test_redact_payload_handles_list(self):
        payload = [{"token": "abc"}, {"host": "db"}]
        sanitized = self.r.redact_payload(payload)
        assert sanitized[0]["token"] == "[REDACTED:key-name]"
        assert sanitized[1]["host"] == "db"


# ── SecretBroker ──────────────────────────────────────────────────────────────

class TestSecretBroker:
    def setup_method(self):
        self.broker = SecretBroker()

    def _request(self, **kwargs):
        defaults = dict(
            service_id="checkout-api",
            environment="dev",
            secret_ref="db/password",
            purpose="runtime",
            requester="aria",
        )
        defaults.update(kwargs)
        return SecretRequest(**defaults)

    def test_lease_is_issued_with_correct_fields(self):
        result = self.broker.request_secret_lease(self._request())
        assert result["status"] == "lease_issued"
        assert "lease" in result
        lease = result["lease"]
        assert lease["secret_ref"] == "db/password"
        assert lease["provider"] == "vault"
        assert lease["ttl_seconds"] == 900
        assert lease["expires_at_epoch"] > 0

    def test_raw_secret_is_never_returned(self):
        result = self.broker.request_secret_lease(self._request())
        assert result["raw_secret_returned"] is False
        assert result["lease"]["value_available"] is False

    def test_safety_block_is_present(self):
        result = self.broker.request_secret_lease(self._request())
        safety = result["safety"]
        assert safety["prompt_safe"] is True
        assert safety["store_raw_secret"] is False
        assert safety["redact_before_rag"] is True

    def test_lease_id_encodes_context(self):
        result = self.broker.request_secret_lease(self._request())
        lease_id = result["lease"]["lease_id"]
        assert "checkout-api" in lease_id
        assert "dev" in lease_id

    def test_missing_service_id_raises(self):
        with pytest.raises(ValueError, match="service_id"):
            self.broker.request_secret_lease(
                SecretRequest(service_id="", environment="dev", secret_ref="x", purpose="runtime")
            )

    def test_missing_secret_ref_raises(self):
        with pytest.raises(ValueError):
            self.broker.request_secret_lease(
                SecretRequest(service_id="svc", environment="dev", secret_ref="", purpose="runtime")
            )


# ── SecretGovernanceAgent ─────────────────────────────────────────────────────

class TestSecretGovernanceAgent:
    def setup_method(self):
        self.agent = SecretGovernanceAgent()

    def test_clean_payload_scores_a(self):
        result = self.agent.review({"service_id": "api", "environment": "dev"})
        assert result["score"] == "A"
        assert result["findings"] == []

    def test_exposed_github_token_scores_c(self):
        result = self.agent.review({"token": "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabc123"})
        assert result["score"] == "C"
        assert any(f["severity"] == "P1" for f in result["findings"])

    def test_detects_ci_static_secret_pattern(self):
        result = self.agent.review({"pipeline": "env: API_KEY: ${{ secrets.API_KEY }}"})
        assert any(f["category"] == "cicd" for f in result["findings"])

    def test_detects_k8s_secretkeyref(self):
        result = self.agent.review({"manifest": "env:\n  - name: DB_PASS\n    valueFrom:\n      secretKeyRef:\n        name: db-secret"})
        assert any(f["category"] == "kubernetes" for f in result["findings"])

    def test_response_always_has_controls(self):
        result = self.agent.review({})
        assert "controls" in result
        assert "never_store_raw_secrets" in result["controls"]

    def test_sanitize_for_rag_redacts_and_allows_indexing(self):
        doc = {"content": "normal text", "api_key": "supersecret"}
        result = self.agent.sanitize_for_rag(doc)
        assert result["rag_index_allowed"] is True
        assert result["raw_secret_retained"] is False
        assert result["sanitized"]["api_key"] == "[REDACTED:key-name]"

    def test_sanitized_preview_truncated_to_2000_chars(self):
        result = self.agent.review({"blob": "x" * 5000})
        assert len(result["sanitized_preview"]) <= 2000
