from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class LLMGuardrails:
    """Post-processes LLM output to reduce hallucination risk.

    The guardrail does not claim semantic truth. It enforces a conservative
    contract: answers must point to retrieved sources/evidence and dangerous
    execution is never allowed directly from LLM output.
    """
    min_sources_for_actionable: int = 1

    def apply(self, llm_result: dict[str, Any], rag_answer: dict[str, Any], evidence: list[dict] | None = None) -> dict:
        sources = rag_answer.get("sources") if isinstance(rag_answer, dict) else []
        evidence = evidence or []
        grounded = bool(sources) or bool(evidence)
        recommendation = llm_result.get("recommended_action") or llm_result.get("recommendation") or "investigate"
        can_be_actionable = grounded and not self._looks_like_direct_execution(recommendation)
        return {
            **llm_result,
            "guardrails": {
                "grounded": grounded,
                "source_count": len(sources or []),
                "evidence_count": len(evidence),
                "actionable": can_be_actionable,
                "blocked_reason": None if can_be_actionable else "No retrieved/evidence grounding or response attempted direct execution.",
                "execution_boundary": "LLM can recommend only. ReBAC + policy + approval + executor own mutations.",
            },
        }

    def validate_text(self, answer: str, sources: list | None = None, evidence: list | None = None) -> dict:
        sources = sources or []
        evidence = evidence or []
        grounded = bool(sources) or bool(evidence)
        return {
            "grounded": grounded,
            "source_count": len(sources),
            "evidence_count": len(evidence),
            "verdict": "allowed" if grounded else "needs_sources",
            "message": "Answer has grounding evidence." if grounded else "Answer should not be treated as factual until linked to RAG sources or telemetry evidence.",
        }

    def _looks_like_direct_execution(self, text: str) -> bool:
        lowered = str(text).lower()
        dangerous = ["kubectl delete", "terraform apply", "terraform destroy", "delete namespace", "drop database"]
        return any(term in lowered for term in dangerous)
