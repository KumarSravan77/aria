from server.observability.correlator import ObservabilityCorrelator
from server.slo.burn_rate_alerts import SloBurnRateAlertEngine
from server.slo.slo_engine import SloEngine
from server.chaos.scheduler import ChaosScheduler
from server.chaos.resilience_trending import ResilienceTrending
from server.security_runtime.policy_violation_ingestor import PolicyViolationIngestor
from server.chatops.interactive_approvals import InteractiveApprovalBuilder
from server.llm.guardrails import LLMGuardrails

class Unavailable:
    def query(self, *_args, **_kwargs):
        raise RuntimeError("not configured")
    def search_service_traces(self, *_args, **_kwargs):
        raise RuntimeError("not configured")
    def service_topology(self, *_args, **_kwargs):
        return {"available": False, "reason": "hubble not wired"}


def test_observability_correlator_degrades_gracefully():
    result = ObservabilityCorrelator(Unavailable(), Unavailable(), Unavailable(), Unavailable()).correlate("checkout-api")
    assert result["service"] == "checkout-api"
    assert len(result["evidence"]) == 5
    assert result["probable_cause"] in {"insufficient_observability_evidence", "needs_human_correlation"}


def test_slo_burn_alert_produces_alertmanager_payload():
    result = SloBurnRateAlertEngine(SloEngine()).evaluate("checkout-api", total_requests=1000, failed_requests=100)
    assert result["alert"] is True
    assert result["alertmanager_payload"]["alerts"][0]["labels"]["service"] == "checkout-api"


def test_chaos_schedule_is_plan_only():
    plan = ChaosScheduler().plan_weekly("checkout-api", experiments=["pod-delete"])
    assert plan["enabled"] is False
    assert "RRULE" in plan["schedule"]


def test_resilience_trending_reads_memory_items():
    trend = ResilienceTrending().trend("checkout-api", {"items": [{"outcome": "recovered", "metadata": {"resilience_score": 90}}]})
    assert trend["average_resilience_score"] == 90
    assert trend["trend"] == "improving"


def test_policy_violation_ingestor_normalizes_kyverno():
    incidents = PolicyViolationIngestor().normalize_kyverno({"service": "checkout-api", "policy": "require-probes", "message": "missing readiness"})
    assert incidents[0]["source"] == "kyverno"
    assert incidents[0]["service"] == "checkout-api"


def test_chatops_approval_card_does_not_bypass_controls():
    card = InteractiveApprovalBuilder().build(1, "INC-1", {"action": "argocd_sync", "target": "checkout-api"}, "sre-a")
    assert "/aria approve 1" in card["actions"][0]["command"]
    assert "do not bypass" in card["safety"]


def test_llm_guardrails_require_grounding():
    result = LLMGuardrails().validate_text("rollback now", sources=[], evidence=[])
    assert result["verdict"] == "needs_sources"
    grounded = LLMGuardrails().apply({"recommended_action": "rollback"}, {"sources": [{"title": "runbook"}]})
    assert grounded["guardrails"]["grounded"] is True
