from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.evals.k8s_issues_dataset.importer import K8sIssuesImporter
from server.evals.k8s_issues_dataset.normalizer import K8sIssueNormalizer
from server.evals.scoring.evaluation_scorecard import EvaluationScorecard

try:
    from server.investigation.langgraph.graph import LangGraphInvestigationWorkflow
except Exception:  # pragma: no cover
    LangGraphInvestigationWorkflow = None


@dataclass
class K8sIssueReplayRunner:
    importer: K8sIssuesImporter = field(default_factory=K8sIssuesImporter)
    normalizer: K8sIssueNormalizer = field(default_factory=K8sIssueNormalizer)

    def list_normalized(self) -> dict[str, Any]:
        issues = self.importer.load()
        normalized = self.normalizer.normalize_many(issues)
        return {
            "dataset": "k8s-prod-issues",
            "count": len(normalized),
            "issues": normalized,
        }

    def replay(self, limit: int = 10) -> dict[str, Any]:
        normalized = self.normalizer.normalize_many(self.importer.load())[:limit]
        results = []
        for item in normalized:
            if LangGraphInvestigationWorkflow is None:
                graph_result = {"available": False, "reason": "LangGraphInvestigationWorkflow unavailable"}
            else:
                graph_result = LangGraphInvestigationWorkflow().invoke(item["incident"])
            route = graph_result.get("summary", {}).get("route", []) if isinstance(graph_result, dict) else []
            results.append({
                "id": item["id"],
                "failure_mode": item["failure_mode"],
                "service": item["service"],
                "severity": item["severity"],
                "safe_for_training": item["safety"]["safe_for_training"],
                "needs_review": item["needs_review"],
                "route": route,
                "k8s_troubleshooter_used": "kubernetes_troubleshooter" in route,
                "scorecard": EvaluationScorecard().score(route=route, expected_nodes=["metrics", "logs", "rca"], expected_rca=item.get("expected_root_cause"), recommendation=item.get("expected_remediation") or ""),
                "istio_used": "istio" in route,
                "thanos_used": "thanos" in route,
            })

        return {
            "dataset": "k8s-prod-issues",
            "replayed": len(results),
            "results": results,
            "safety_note": "Dataset scenarios are eval/training inputs, not trusted production runbooks until reviewed.",
        }
