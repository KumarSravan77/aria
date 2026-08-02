from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.evals.k8s_issues_dataset.classifier import K8sIssueClassifier
from server.evals.k8s_issues_dataset.safety_filter import K8sIssueSafetyFilter


@dataclass
class K8sIssueNormalizer:
    classifier: K8sIssueClassifier = field(default_factory=K8sIssueClassifier)
    safety: K8sIssueSafetyFilter = field(default_factory=K8sIssueSafetyFilter)

    def normalize(self, issue: dict[str, Any]) -> dict[str, Any]:
        failure_mode = self.classifier.classify(issue)
        safety = self.safety.evaluate(issue)
        symptoms = issue.get("symptoms", [])
        service = issue.get("service", "unknown-service")
        severity = issue.get("severity", "P3")

        return {
            "id": issue.get("id"),
            "title": issue.get("title", "Kubernetes production issue"),
            "service": service,
            "severity": severity,
            "failure_mode": failure_mode,
            "signals": symptoms + [failure_mode],
            "symptoms": symptoms,
            "expected_root_cause": issue.get("root_cause"),
            "expected_remediation": issue.get("safe_remediation"),
            "training_only": safety["training_only"],
            "source_verified": safety["source_verified"],
            "needs_review": safety["needs_review"],
            "safety": safety,
            "incident": {
                "incident_id": issue.get("id"),
                "service": service,
                "severity": severity,
                "signals": symptoms + [failure_mode],
                "source": "k8s-prod-issues-dataset",
            },
        }

    def normalize_many(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.normalize(issue) for issue in issues]
