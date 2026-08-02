"""Tests for the 5 intelligence-layer modules: remediation scorer, RL optimizer,
temporal clusterer, incident forecaster, and remediation ranker agent."""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.db.session import Base
from server.memory.remediation_scorer import RemediationScorer
from server.memory.rl_optimizer import RLOptimizer
from server.forecasting.incident_forecaster import IncidentForecaster
from server.agents.remediation_ranker import RemediationRankerAgent
from server.healing.policy_validator import PolicyValidator
from server.correlation.temporal_clusterer import TemporalClusterer

POLICY = Path(__file__).resolve().parents[1] / "server" / "healing" / "policies" / "self_healing_policy.yaml"


def make_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


# ── RemediationScorer ──────────────────────────────────────────────────────

class TestRemediationScorer:
    def test_returns_empty_for_no_memory(self):
        assert RemediationScorer().score({"service": "svc"}, []) == {}

    def test_scores_similar_incident_higher(self):
        memory = [
            {"remediation": "scale_deployment", "outcome": "mitigated",
             "metadata": {"symptoms": ["high latency"], "signals": {"cpu_percent": 85}}},
            {"remediation": "rollback_deployment", "outcome": "escalated",
             "metadata": {"symptoms": ["disk full"], "signals": {}}},
        ]
        incident = {"symptoms": ["high latency"], "signals": {"cpu_percent": 88}}
        scores = RemediationScorer().score(incident, memory)
        assert "scale_deployment" in scores
        assert scores.get("scale_deployment", 0) > scores.get("rollback_deployment", 0)

    def test_low_similarity_items_are_ignored(self):
        memory = [
            {"remediation": "scale_deployment", "outcome": "mitigated",
             "metadata": {"symptoms": ["disk full"], "signals": {"cpu_percent": 10}}},
        ]
        incident = {"symptoms": ["high latency"], "signals": {"error_rate_percent": 20}}
        scores = RemediationScorer().score(incident, memory)
        # similarity < 0.1 → filtered out → no scores
        assert scores.get("scale_deployment", 0) == 0.0 or "scale_deployment" not in scores

    def test_failed_outcomes_score_lower_than_successful(self):
        memory = [
            {"remediation": "restart_deployment", "outcome": "mitigated",
             "metadata": {"symptoms": ["high latency"]}},
            {"remediation": "rollback_deployment", "outcome": "unresolved",
             "metadata": {"symptoms": ["high latency"]}},
        ]
        scores = RemediationScorer().score({"symptoms": ["high latency"]}, memory)
        assert scores.get("restart_deployment", 0) > scores.get("rollback_deployment", 0)


# ── RLOptimizer ────────────────────────────────────────────────────────────

class TestRLOptimizer:
    def test_unexplored_actions_get_max_exploration_score(self):
        rl = RLOptimizer()
        ranked = rl.recommend("svc", "unknown", "P1", ["scale_deployment"])
        assert ranked[0]["ucb_score"] == 99.0
        assert ranked[0]["trials"] == 0

    def test_successful_action_increases_mean_reward(self):
        rl = RLOptimizer()
        for _ in range(3):
            rl.update("checkout-api", "deployment_regression", "P1",
                      "rollback_deployment", success=True, mttr_seconds=45)
        ranked = rl.recommend("checkout-api", "deployment_regression", "P1",
                               ["rollback_deployment", "scale_deployment"])
        rollback = next(r for r in ranked if r["action"] == "rollback_deployment")
        assert rollback["mean_reward"] > 1.0
        assert rollback["trials"] == 3

    def test_failed_actions_lower_mean_reward(self):
        rl = RLOptimizer()
        rl.update("svc", "resource_saturation", "P2", "restart_deployment", success=False)
        rl.update("svc", "resource_saturation", "P2", "scale_deployment", success=True)
        ranked = rl.recommend("svc", "resource_saturation", "P2",
                               ["restart_deployment", "scale_deployment"])
        actions = [r["action"] for r in ranked]
        # scale_deployment has higher mean reward; after enough trials UCB should prefer it
        scale = next(r for r in ranked if r["action"] == "scale_deployment")
        restart = next(r for r in ranked if r["action"] == "restart_deployment")
        assert scale["mean_reward"] > restart["mean_reward"]

    def test_state_count_increments(self):
        rl = RLOptimizer()
        rl.update("svc-a", "unknown", "P1", "scale_deployment", success=True)
        rl.update("svc-b", "unknown", "P1", "scale_deployment", success=True)
        assert rl.state_count() == 2


# ── IncidentForecaster ─────────────────────────────────────────────────────

class TestIncidentForecaster:
    def test_healthy_service_predicts_none(self):
        result = IncidentForecaster().forecast(
            "svc", {"burn_rate": 0.1, "error_budget_remaining": 99.0}, [], 0)
        assert result["prediction"] == "none"
        assert result["confidence"] < 0.2

    def test_critical_burn_rate_predicts_high(self):
        result = IncidentForecaster().forecast(
            "checkout-api", {"burn_rate": 15.0, "error_budget_remaining": 0.0}, [], 0)
        assert result["prediction"] == "high"
        assert result["confidence"] >= 0.6

    def test_cluster_pressure_increases_confidence(self):
        base = IncidentForecaster().forecast("svc", {"burn_rate": 2.5, "error_budget_remaining": 20.0}, [], 0)
        with_cluster = IncidentForecaster().forecast("svc", {"burn_rate": 2.5, "error_budget_remaining": 20.0}, [], 5)
        assert with_cluster["confidence"] > base["confidence"]

    def test_memory_escalations_increase_confidence(self):
        items_bad = [{"outcome": "escalated"}, {"outcome": "paged"}, {"outcome": "paged"}]
        result = IncidentForecaster().forecast("svc", {"burn_rate": 1.5, "error_budget_remaining": 50.0}, items_bad, 0)
        assert result["factors"]["recent_escalations"] == 3
        assert result["confidence"] > 0.2


# ── TemporalClusterer ──────────────────────────────────────────────────────

class TestTemporalClusterer:
    def test_single_incident_is_not_a_cluster(self):
        db = make_db()
        result = TemporalClusterer().cluster("checkout-api", db)
        assert result["is_cluster"] is False
        assert result["cluster_size"] == 0

    def test_cluster_detected_with_three_or_more_incidents(self):
        from server.db.models import Incident
        db = make_db()
        for i in range(3):
            row = Incident(id=f"INC-CLU-{i}", service="checkout-api",
                           environment="prod", severity="P1", payload={})
            db.add(row)
        db.commit()
        result = TemporalClusterer().cluster("checkout-api", db)
        assert result["is_cluster"] is True
        assert result["cluster_size"] == 3

    def test_different_service_not_included(self):
        from server.db.models import Incident
        db = make_db()
        for i in range(3):
            row = Incident(id=f"INC-SVC-{i}", service="payment-api",
                           environment="prod", severity="P1", payload={})
            db.add(row)
        db.commit()
        result = TemporalClusterer().cluster("checkout-api", db)
        assert result["cluster_size"] == 0


# ── RemediationRankerAgent ─────────────────────────────────────────────────

class TestRemediationRankerAgent:
    def _make_ranker(self):
        return RemediationRankerAgent(PolicyValidator(POLICY), RemediationScorer(), RLOptimizer())

    def test_returns_agent_result_with_ranking(self):
        result = self._make_ranker().run(
            {"service": "checkout-api", "environment": "dev", "severity": "P2"},
            context={"user": {"role": "sre", "team": "platform"}, "memory_items": []},
        )
        assert result.agent == "remediation_ranker"
        assert result.available is True
        assert len(result.evidence) == 1
        ranking = result.evidence[0]["ranked"]
        assert len(ranking) > 0
        assert "action" in ranking[0]
        assert "confidence" in ranking[0]

    def test_ranking_has_safety_boundary_in_recommendations(self):
        result = self._make_ranker().run(
            {"service": "checkout-api", "environment": "dev"},
            context={"user": {"role": "sre", "team": "platform"}, "memory_items": []},
        )
        combined = " ".join(result.recommendations).lower()
        assert "dry_run" in combined or "approval" in combined

    def test_rl_learns_and_influences_ranking(self):
        scorer = RemediationScorer()
        rl = RLOptimizer()
        ranker = RemediationRankerAgent(PolicyValidator(POLICY), scorer, rl)
        incident = {"service": "checkout-api", "environment": "dev",
                    "severity": "P1", "probable_cause": "resource_saturation"}
        ctx = {"user": {"role": "sre", "team": "platform"}, "memory_items": []}

        # Teach RL that scale_deployment is highly successful for this state
        for _ in range(5):
            rl.update("checkout-api", "resource_saturation", "P1",
                      "scale_deployment", success=True, mttr_seconds=30)
        for _ in range(3):
            rl.update("checkout-api", "resource_saturation", "P1",
                      "restart_deployment", success=False)

        result = ranker.run(incident, context=ctx)
        ranking = result.evidence[0]["ranked"]
        top = ranking[0]["action"]
        # After learning, scale_deployment should rank at or near the top
        assert top == "scale_deployment" or ranking[0]["rl_mean_reward"] >= ranking[-1]["rl_mean_reward"]
