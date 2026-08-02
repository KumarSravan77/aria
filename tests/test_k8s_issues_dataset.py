from server.evals.k8s_issues_dataset.classifier import K8sIssueClassifier
from server.evals.k8s_issues_dataset.safety_filter import K8sIssueSafetyFilter
from server.evals.k8s_issues_dataset.normalizer import K8sIssueNormalizer
from server.evals.k8s_issues_dataset.replay_runner import K8sIssueReplayRunner


def test_classifier_detects_crashloop():
    assert K8sIssueClassifier().classify({"symptoms": ["CrashLoopBackOff"]}) == "CrashLoopBackOff"


def test_safety_filter_blocks_destructive_action():
    result = K8sIssueSafetyFilter().evaluate({"remediation": "kubectl delete namespace prod"})
    assert result["safe_for_training"] is False
    assert result["decision"] == "block_until_reviewed"


def test_normalizer_outputs_aria_incident():
    result = K8sIssueNormalizer().normalize({
        "id": "x",
        "service": "checkout-api",
        "severity": "P2",
        "symptoms": ["OOMKilled"],
        "root_cause": "memory_limit",
        "safe_remediation": "increase_memory",
    })
    assert result["failure_mode"] == "OOMKilled"
    assert result["incident"]["service"] == "checkout-api"


def test_replay_runner_loads_sample_dataset():
    result = K8sIssueReplayRunner().list_normalized()
    assert result["count"] >= 1
    assert result["issues"][0]["training_only"] is True
