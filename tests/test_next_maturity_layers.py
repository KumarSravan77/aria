from server.ai_observability.hallucination_metrics import HallucinationMetrics
from server.evals.benchmark_runner import BenchmarkRunner
from server.gitops_ai.remediation_service import GitOpsRemediationService
from server.observability.trace_causality import TraceCausalityEngine
from server.memory.pattern_detector import PatternDetector


def test_hallucination_metrics_requires_sources():
    result = HallucinationMetrics().score("rollback deployment", [])
    assert result["verdict"] == "needs_sources"


def test_static_benchmark_runs():
    result = BenchmarkRunner().run_static_benchmark()
    assert result["count"] >= 1
    assert result["average_score"] > 0


def test_gitops_remediation_dry_run():
    result = GitOpsRemediationService().propose("checkout-api", "latency regression", dry_run=True)
    assert result["pull_request"]["dry_run"] is True


def test_trace_causality_detects_deployment_regression():
    result = TraceCausalityEngine().infer([{"deployment": "abc123"}, {"latency": "high"}])
    assert "possible_deployment_regression" in result["causal_hypotheses"]


def test_pattern_detector_recurring():
    records = [{"root_cause": "deployment_regression"} for _ in range(3)]
    result = PatternDetector().detect(records)
    assert result["pattern"] == "recurring"
