from server.ai_observability.evaluation_runner import EvaluationRunner
from server.evals.benchmark_runner import BenchmarkRunner
from server.gitops_ai.remediation_service import GitOpsRemediationService
from server.memory.pattern_detector import PatternDetector
from server.security_runtime.security_reasoner import SecurityReasoner

def test_ai_evaluation_needs_sources():
    result = EvaluationRunner().groundedness("rollback deployment", [])
    assert result["verdict"] == "needs_sources"

def test_synthetic_benchmark_runs():
    result = BenchmarkRunner().run()
    assert result["count"] == 3
    assert result["average_score"] > 0

def test_gitops_ai_proposal_is_dry_run():
    result = GitOpsRemediationService().propose("checkout-api", "latency regression")
    assert result["pull_request"]["dry_run"] is True
    assert "safety_boundary" in result

def test_pattern_detector_recurring():
    result = PatternDetector().detect([{"root_cause": "deployment_regression"} for _ in range(3)])
    assert result["pattern"] == "recurring"

def test_security_reasoner_privileged():
    result = SecurityReasoner().analyze({"message": "privileged container detected"})
    assert "privileged_container_policy_violation" in result["hypotheses"]
