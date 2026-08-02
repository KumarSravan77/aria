from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class K8sIssueSafetyFilter:
    forbidden_patterns: tuple[str, ...] = (
        "delete namespace",
        "kubectl delete ns",
        "delete pvc",
        "delete pv",
        "terraform destroy",
        "disable networkpolicy",
        "disable kyverno",
        "disable gatekeeper",
        "bypass approval",
        "force delete",
    )

    def evaluate(self, issue: dict[str, Any]) -> dict[str, Any]:
        text = str(issue).lower()
        hits = [p for p in self.forbidden_patterns if p in text]
        return {
            "safe_for_training": not hits,
            "unsafe_patterns": hits,
            "training_only": bool(issue.get("training_only", True)),
            "source_verified": bool(issue.get("source_verified", False)),
            "needs_review": bool(hits) or not bool(issue.get("source_verified", False)),
            "decision": "allow_for_eval_only" if not hits else "block_until_reviewed",
        }
