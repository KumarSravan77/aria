from server.safety.dry_run_policy import DryRunPolicy
from server.safety.mutation_guard import MutationGuard
from server.investigation.langgraph.state_utils import dedupe_evidence, route_budget
from server.evals.scoring.evaluation_scorecard import EvaluationScorecard
from server.ai_observability.trace_sampling import TraceSamplingPolicy
from server.memory.compaction import MemoryCompactor


def test_dry_run_blocks_execution():
    decision = DryRunPolicy().enforce(dry_run=True, approved=False, risk="high")
    assert decision.execution_allowed is False
    assert decision.mode == "recommendation_only"


def test_mutation_guard_blocks_dangerous_text():
    result = MutationGuard().scan_text("kubectl delete namespace prod")
    assert result["safe"] is False


def test_dedupe_evidence_removes_duplicates():
    evidence = [{"node": "kafka", "type": "x", "summary": "same"}, {"node": "kafka", "type": "x", "summary": "same"}]
    assert len(dedupe_evidence(evidence)) == 1


def test_route_budget_caps_and_preserves_core():
    route = ["metrics", "logs", "traces", "kafka", "istio", "thanos", "security", "rag", "rca", "healing", "chatops"]
    budgeted = route_budget(route, max_specialists=3)
    assert "metrics" in budgeted
    assert "logs" in budgeted
    assert "rca" in budgeted
    assert len(budgeted) <= 8


def test_scorecard_passes_good_result():
    result = EvaluationScorecard().score(
        route=["metrics", "logs", "kafka", "rca"],
        expected_nodes=["metrics", "logs", "kafka", "rca"],
        predicted_rca="consumer_lag_growth",
        expected_rca="consumer_lag_growth",
        recommendation="rollback after approval",
    )
    assert result["verdict"] == "pass"


def test_trace_sampling_p1_always_true():
    assert TraceSamplingPolicy().should_trace("incident-1", "P1") is True


def test_memory_compactor_summarizes():
    result = MemoryCompactor().compact([{"service": "a", "root_cause": "x"}, {"service": "a", "root_cause": "x"}])
    assert result["input_records"] == 2
    assert result["summary_count"] == 1
