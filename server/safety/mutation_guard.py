from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MutationGuard:
    dangerous_terms: tuple[str, ...] = (
        "kubectl delete namespace",
        "kubectl delete ns",
        "delete pvc",
        "delete pv",
        "terraform destroy",
        "disable kyverno",
        "disable gatekeeper",
        "bypass approval",
        "drop database",
        "truncate table",
        "reset offsets",
        "delete topic",
    )

    def scan_text(self, text: str) -> dict:
        lowered = text.lower()
        hits = [term for term in self.dangerous_terms if term in lowered]
        return {
            "safe": not hits,
            "dangerous_terms": hits,
            "decision": "allow" if not hits else "block_or_manual_review",
        }

    def assert_safe_recommendation(self, text: str) -> dict:
        result = self.scan_text(text)
        result["safety_boundary"] = "Recommendations only; mutation still requires ReBAC, policy, approval, validation and audit."
        return result
