from pathlib import Path

from server.evals.benchmark_runner import BenchmarkRunner
from server.gitops_ai.remediation_service import GitOpsRemediationService
from server.ai_observability.evaluation_runner import EvaluationRunner


def test_gitignore_exists():
    assert Path(".gitignore").exists()


def test_benchmark_runner():
    result = BenchmarkRunner().run_static_benchmark()
    assert result["count"] >= 3
    assert result["average_score"] > 0


def test_gitops_ai_propose_dry_run():
    result = GitOpsRemediationService().propose("checkout-api", "latency regression")
    assert result["pull_request"]["dry_run"] is True


def test_grounding_needs_sources_without_sources():
    result = EvaluationRunner().evaluate_grounding("rollback deployment", [])
    assert result["verdict"] == "needs_sources"
