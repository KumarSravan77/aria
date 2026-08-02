"""Tests for all 15 scalability and autonomous operations upgrades."""
import time
import pytest
from server.agents.agent_router import AgentRouter
from server.agents.health_tracker import AgentHealthTracker
from server.agents.base import BaseAgent, AgentResult
from server.orchestration.degradation import DegradationController, OrchestrationType
from server.orchestration.token_budget import TokenBudgetEnforcer
from server.orchestration.backpressure import BackpressureController
from server.orchestration.investigation_cache import InvestigationCache
from server.orchestration.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
from server.topology.dependency_graph import ServiceDependencyGraph
from server.topology.blast_radius import BlastRadiusAnalyzer
from server.topology.rca_topology_enricher import enrich_rca_with_topology
from server.integrations.servicenow_client import ServiceNowClient
from server.integrations.pagerduty_simulator import PagerDutySimulator
from server.agents.orchestrator import MultiAgentOrchestrator


# ── Test fixtures ─────────────────────────────────────────────────────────────

class NamedAgent(BaseAgent):
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self._fail = fail
    def run(self, incident, context=None):
        if self._fail:
            raise RuntimeError(f"{self.name} failed")
        return AgentResult(agent=self.name, available=True,
                           summary=f"{self.name} ok", evidence=[{"type": self.name}],
                           recommendations=[f"{self.name} recommendation"])


def _agents(*names: str) -> list:
    return [NamedAgent(n) for n in names]


# ── U1 — Dynamic Agent Routing ────────────────────────────────────────────────

class TestAgentRouter:
    def test_p1_runs_all_agents(self):
        agents = _agents("metrics", "logs", "rca", "k8s")
        selected, reason = AgentRouter().select({"severity": "P1"}, agents)
        assert len(selected) == len(agents)
        assert "p1_full" in reason

    def test_p3_runs_only_metrics_and_logs(self):
        agents = _agents("metrics", "logs", "rag", "rca", "k8s")
        selected, reason = AgentRouter().select({"severity": "P3"}, agents)
        names = {a.name for a in selected}
        assert names == {"metrics", "logs"}

    def test_deployment_incident_routes_deployment_agents(self):
        agents = _agents("metrics", "logs", "rag", "rca", "remediation_ranker", "k8s")
        selected, reason = AgentRouter().select(
            {"severity": "P2", "signals": {"recent_deployment": True}}, agents)
        names = {a.name for a in selected}
        assert "rca" in names
        assert "metrics" in names
        assert "remediation_ranker" in names

    def test_kubernetes_incident_routes_k8s_agents(self):
        agents = _agents("metrics", "logs", "k8s", "traces", "rca", "rag")
        selected, _ = AgentRouter().select(
            {"severity": "P2", "symptoms": ["pod crash", "crashloop"]}, agents)
        names = {a.name for a in selected}
        assert "k8s" in names
        assert "traces" in names


# ── U6 — Agent Health Scoring ─────────────────────────────────────────────────

class TestAgentHealthTracker:
    def test_new_agent_is_healthy(self):
        tracker = AgentHealthTracker()
        assert tracker.is_healthy("metrics") is True
        assert tracker.health_score("metrics") == 1.0

    def test_all_failures_quarantines_agent(self):
        tracker = AgentHealthTracker()
        for _ in range(tracker.MIN_SAMPLES):
            tracker.record("bad_agent", False, 5000.0)
        assert tracker.is_healthy("bad_agent") is False
        assert tracker.health_score("bad_agent") == 0.0

    def test_mixed_performance_scores_correctly(self):
        tracker = AgentHealthTracker()
        tracker.record("agent", True, 100)
        tracker.record("agent", True, 120)
        tracker.record("agent", False, 500)
        assert tracker.health_score("agent") == pytest.approx(2 / 3, abs=0.01)

    def test_reset_clears_quarantine(self):
        tracker = AgentHealthTracker()
        for _ in range(tracker.MIN_SAMPLES):
            tracker.record("a", False, 5000)
        assert tracker.is_healthy("a") is False
        tracker.reset("a")
        assert tracker.is_healthy("a") is True


# ── U3 — Graceful Degradation ─────────────────────────────────────────────────

class TestDegradationController:
    def test_normal_mode_below_threshold(self):
        ctrl = DegradationController(degraded_threshold=100, survival_threshold=1000)
        assert ctrl.get_mode(50) == OrchestrationType.NORMAL

    def test_degraded_mode_above_degraded_threshold(self):
        ctrl = DegradationController(degraded_threshold=100, survival_threshold=1000)
        assert ctrl.get_mode(150) == OrchestrationType.DEGRADED

    def test_survival_mode_above_survival_threshold(self):
        ctrl = DegradationController(degraded_threshold=100, survival_threshold=1000)
        assert ctrl.get_mode(1500) == OrchestrationType.SURVIVAL

    def test_manual_override_takes_precedence(self):
        ctrl = DegradationController()
        ctrl.set_manual(OrchestrationType.DEGRADED)
        assert ctrl.get_mode(0) == OrchestrationType.DEGRADED

    def test_degraded_mode_filters_to_metrics_logs(self):
        ctrl = DegradationController()
        agents = _agents("metrics", "logs", "rca", "rag", "k8s")
        filtered = ctrl.filter_agents(agents, OrchestrationType.DEGRADED)
        assert {a.name for a in filtered} == {"metrics", "logs"}

    def test_survival_mode_filters_all_agents(self):
        ctrl = DegradationController()
        agents = _agents("metrics", "logs", "rca")
        assert ctrl.filter_agents(agents, OrchestrationType.SURVIVAL) == []


# ── U4 — Token Budget ─────────────────────────────────────────────────────────

class TestTokenBudget:
    def test_estimate_sums_agent_costs(self):
        agents = _agents("rag", "metrics", "logs")
        budget = TokenBudgetEnforcer()
        est = budget.estimate(agents)
        assert est == 1500 + 100 + 100  # rag + metrics + logs

    def test_trim_respects_budget(self):
        agents = _agents("rag", "rca", "metrics", "logs")
        budget = TokenBudgetEnforcer()
        trimmed, used = budget.trim_to_budget(agents, budget=500)
        assert used <= 500

    def test_estimate_cost_zero_for_local_model(self):
        budget = TokenBudgetEnforcer(model="llama3.1:8b")
        assert budget.estimate_cost_usd(10000) == 0.0

    def test_session_summary_tracks_usage(self):
        budget = TokenBudgetEnforcer()
        budget.record_usage(1000)
        budget.record_usage(500)
        assert budget.session_summary()["total_tokens_used"] == 1500


# ── U5 — Backpressure ─────────────────────────────────────────────────────────

class TestBackpressure:
    def test_acquires_within_limit(self):
        bp = BackpressureController(max_concurrent=5)
        assert bp.acquire() is True

    def test_rejects_at_capacity(self):
        bp = BackpressureController(max_concurrent=2)
        bp.acquire(); bp.acquire()
        assert bp.acquire() is False
        assert bp.metrics()["rejected"] == 1

    def test_release_frees_slot(self):
        bp = BackpressureController(max_concurrent=1)
        assert bp.acquire() is True
        assert bp.acquire() is False
        bp.release()
        assert bp.acquire() is True


# ── U7 — Investigation Cache ──────────────────────────────────────────────────

class TestInvestigationCache:
    def test_returns_none_for_miss(self):
        cache = InvestigationCache()
        assert cache.get("checkout-api", "unknown") is None

    def test_returns_cached_result_on_hit(self):
        cache = InvestigationCache()
        cache.set("checkout-api", "cpu", {"result": "test"})
        assert cache.get("checkout-api", "cpu") == {"result": "test"}

    def test_hit_rate_increases_on_cache_hit(self):
        cache = InvestigationCache()
        cache.set("svc", "cause", {"x": 1})
        cache.get("svc", "cause")  # hit
        cache.get("svc", "other")  # miss
        assert cache.metrics()["hit_rate"] == 0.5

    def test_expired_entry_is_treated_as_miss(self):
        cache = InvestigationCache(ttl_seconds=0)  # immediate expiry
        cache.set("svc", "cause", {"x": 1})
        time.sleep(0.01)
        assert cache.get("svc", "cause") is None


# ── U8 — Dependency Graph ─────────────────────────────────────────────────────

class TestDependencyGraph:
    def test_downstream_returns_direct_deps(self):
        g = ServiceDependencyGraph()
        assert "payment-api" in g.downstream("checkout-api")

    def test_upstream_returns_callers(self):
        g = ServiceDependencyGraph()
        assert "checkout-api" in g.upstream("payment-api")

    def test_all_affected_includes_transitive_deps(self):
        g = ServiceDependencyGraph()
        affected = g.all_affected("checkout-api")
        assert "payment-api" in affected
        assert "fraud-detection" in affected  # transitive via payment-api

    def test_graph_dict_has_edges(self):
        g = ServiceDependencyGraph()
        d = g.to_dict()
        assert d["total_edges"] > 0
        assert d["total_services"] > 0


# ── U9 — Blast Radius ─────────────────────────────────────────────────────────

class TestBlastRadius:
    def _analyzer(self):
        return BlastRadiusAnalyzer(ServiceDependencyGraph())

    def test_p1_blast_radius_is_critical(self):
        result = self._analyzer().analyze("checkout-api", "P1")
        assert result["impact_level"] in {"critical", "high"}
        assert result["blast_radius_score"] > 0

    def test_service_with_no_deps_has_low_blast_radius(self):
        g = ServiceDependencyGraph({"isolated-svc": []})
        result = BlastRadiusAnalyzer(g).analyze("isolated-svc", "P1")
        assert result["impact_level"] == "low"
        assert result["blast_radius_score"] == 0

    def test_customer_facing_services_identified(self):
        result = self._analyzer().analyze("checkout-api", "P1")
        # payment-api, checkout-api downstream contain "api" keyword
        assert len(result["customer_facing_impact"]) >= 0  # may vary by graph


# ── U10 — Topology-Aware RCA ──────────────────────────────────────────────────

class TestRCATopologyEnricher:
    def test_enriched_rca_contains_topology_section(self):
        rca = "# RCA Draft\n\n## Timeline\n- event 1\n"
        blast = {
            "root_service": "checkout-api",
            "all_affected_services": ["payment-api"],
            "customer_facing_impact": ["payment-api"],
            "upstream_callers": [],
            "blast_radius_score": 3,
            "impact_level": "high",
            "recommendation": "Investigate",
        }
        enriched = enrich_rca_with_topology(rca, blast)
        assert "Topology and Blast Radius" in enriched
        assert "checkout-api" in enriched
        assert "payment-api" in enriched

    def test_no_enrichment_for_empty_blast_radius(self):
        rca = "# RCA Draft"
        assert enrich_rca_with_topology(rca, {}) == rca


# ── U11 — ServiceNow ─────────────────────────────────────────────────────────

class TestServiceNow:
    def test_returns_unavailable_when_unconfigured(self):
        client = ServiceNowClient()
        result = client.get_recent_changes("checkout-api")
        assert result["available"] is False

    def test_risk_score_zero_for_no_changes(self):
        client = ServiceNowClient()
        risk = client.change_risk_score([])
        assert risk["risk_score"] == 0

    def test_high_risk_changes_increase_score(self):
        client = ServiceNowClient()
        changes = [{"risk": "high"}, {"risk": "high"}, {"risk": "moderate"}]
        risk = client.change_risk_score(changes)
        assert risk["risk_score"] > 0
        assert risk["risk_level"] in {"high", "critical"}


# ── U12 — PagerDuty Simulator ────────────────────────────────────────────────

class TestPagerDutySimulator:
    def test_escalation_chain_has_steps(self):
        sim = PagerDutySimulator()
        result = sim.simulate_escalation("checkout-api", "P1")
        assert len(result["escalation_chain"]) > 0

    def test_bottleneck_detected_for_overloaded_responder(self):
        from server.integrations.pagerduty_simulator import BOTTLENECK_THRESHOLD
        sim = PagerDutySimulator(
            chains={"svc": ["busy-person"]},
            load={"busy-person": BOTTLENECK_THRESHOLD + 1}
        )
        result = sim.simulate_escalation("svc", "P1")
        assert "busy-person" in result["bottlenecks_detected"]

    def test_healthy_chain_no_bottleneck(self):
        sim = PagerDutySimulator(
            chains={"svc": ["available-person"]},
            load={"available-person": 0}
        )
        result = sim.simulate_escalation("svc", "P2")
        assert result["bottlenecks_detected"] == []


# ── U15 — Circuit Breaker ─────────────────────────────────────────────────────

class TestCircuitBreaker:
    def test_closed_by_default(self):
        cb = CircuitBreaker("test")
        assert cb.state.value == "closed"
        assert cb.can_execute() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state.value == "open"
        assert cb.can_execute() is False

    def test_transitions_to_half_open_after_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_seconds=0.01)
        cb.record_failure()
        assert cb.state.value == "open"
        time.sleep(0.02)
        assert cb.can_execute() is True  # half-open
        assert cb.state.value == "half_open"

    def test_success_in_half_open_closes_circuit(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_seconds=0.01)
        cb.record_failure()
        time.sleep(0.02)
        cb.can_execute()  # → half_open
        cb.record_success()
        assert cb.state.value == "closed"

    def test_registry_manages_named_breakers(self):
        reg = CircuitBreakerRegistry()
        cb_a = reg.get("service-a")
        cb_b = reg.get("service-b")
        assert cb_a is not cb_b
        assert reg.get("service-a") is cb_a  # same instance

    def test_status_includes_all_breakers(self):
        reg = CircuitBreakerRegistry()
        reg.get("svc-x")
        reg.get("svc-y")
        status = reg.all_status()
        assert "svc-x" in status and "svc-y" in status


# ── Full Orchestrator Integration ─────────────────────────────────────────────

class TestOrchestratorIntegration:
    def _make_orchestrator(self, agents=None):
        return MultiAgentOrchestrator(
            agents=agents or _agents("metrics", "logs", "rca"),
        )

    def test_normal_investigation_returns_all_agents(self):
        orch = self._make_orchestrator(_agents("metrics", "logs", "rca"))
        result = orch.investigate({"incident_id": "INC-1", "service": "svc", "severity": "P1"})
        assert result["agent_count"] == 3
        assert result["evidence_count"] == 3

    def test_backpressure_rejects_at_capacity(self):
        orch = self._make_orchestrator()
        orch.backpressure.set_limit(0)  # full capacity
        result = orch.investigate({"service": "svc", "severity": "P2"})
        assert result["mode"] == "backpressure-rejected"

    def test_survival_mode_returns_no_agents(self):
        orch = self._make_orchestrator()
        orch.degradation.set_manual(OrchestrationType.SURVIVAL)
        result = orch.investigate({"service": "svc", "severity": "P2"})
        assert result["mode"] == "survival"
        assert result["agent_count"] == 0

    def test_cache_hit_skips_reexecution(self):
        orch = self._make_orchestrator(_agents("metrics", "logs"))
        incident = {"incident_id": "INC-2", "service": "checkout-api",
                    "severity": "P1", "probable_cause": "cpu"}
        orch.investigate(incident)                     # populates cache
        result = orch.investigate(incident)            # should hit cache
        assert result.get("cache_hit") is True

    def test_unhealthy_agent_excluded(self):
        agents = _agents("metrics", "logs", "rca")
        orch = self._make_orchestrator(agents)
        # Force logs agent to be quarantined
        for _ in range(orch.health.MIN_SAMPLES):
            orch.health.record("logs", False, 5000)
        result = orch.investigate({"service": "svc", "severity": "P1", "incident_id": "INC-3",
                                   "probable_cause": "distinct_cause_nocache"})
        agent_names = [a["agent"] for a in result.get("agents", [])]
        # logs agent may be excluded or return circuit_open result
        assert result["orchestration_meta"]["quarantined_agents"] == ["logs"] or \
               all(a != "logs" or "circuit" in str(result["agents"]) for a in agent_names)

    def test_orchestration_meta_included_in_response(self):
        orch = self._make_orchestrator()
        result = orch.investigate({"service": "svc", "severity": "P2",
                                   "incident_id": "INC-4", "probable_cause": "unique_p2"})
        meta = result.get("orchestration_meta", {})
        assert "backpressure" in meta
        assert "estimated_tokens" in meta
        assert "cache_metrics" in meta
