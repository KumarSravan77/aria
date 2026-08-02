from __future__ import annotations
from typing import Any


class RemediationScorer:
    """Scores candidate remediation actions by signal similarity to past successful incidents.

    Uses Jaccard similarity on incident fingerprints — no external dependencies required.
    For production, swap _signal_fingerprint embeddings for ChromaDB vectors.
    """

    def _signal_fingerprint(self, incident: dict[str, Any]) -> frozenset[str]:
        fp: set[str] = set()
        fp.update(s.lower() for s in incident.get("symptoms", []))
        signals = incident.get("signals", {}) or {}
        if float(str(signals.get("cpu_percent", 0)).replace("%", "") or 0) >= 80:
            fp.add("high_cpu")
        if float(str(signals.get("error_rate_percent", 0)).replace("%", "") or 0) >= 5:
            fp.add("high_error_rate")
        if float(str(signals.get("p95_latency_ms", 0)).replace("ms", "") or 0) >= 1000:
            fp.add("high_latency")
        if signals.get("recent_deployment"):
            fp.add("recent_deployment")
        cause = incident.get("probable_cause") or (incident.get("analysis") or {}).get("probable_cause", "")
        if cause:
            fp.add(str(cause))
        return frozenset(fp) or frozenset({"unknown"})

    def _jaccard(self, a: frozenset, b: frozenset) -> float:
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    def score(self, incident: dict[str, Any], memory_items: list[dict[str, Any]]) -> dict[str, float]:
        """Return {remediation_action: confidence_score} ranked by past similarity-weighted success."""
        if not memory_items:
            return {}

        fp = self._signal_fingerprint(incident)
        action_weights: dict[str, list[float]] = {}

        for item in memory_items:
            # Merge metadata into the item so stored context (symptoms, signals) is fingerprinted
            past_fp = self._signal_fingerprint({**item.get("metadata", {}), **item})
            sim = self._jaccard(fp, past_fp)
            if sim < 0.1:
                continue
            action = item.get("remediation", "unknown")
            outcome = item.get("outcome", "unknown").lower()
            # "resolved" would match "unresolved" as a substring; check explicitly
            is_success = (
                "mitigat" in outcome
                or ("resolved" in outcome and "unresolved" not in outcome)
                or "scaled" in outcome
                or "rollback" in outcome
            )
            success_factor = 1.0 if is_success else 0.2
            action_weights.setdefault(action, []).append(sim * success_factor)

        return {
            action: round(sum(scores) / max(len(scores), 1), 3)
            for action, scores in sorted(action_weights.items(), key=lambda x: -sum(x[1]))
        }
