from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


def score_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic demo risk scorer used by tests/examples, not a real fraud model."""
    score = 0.05
    amount = float(transaction.get("amount", 0) or 0)
    velocity = float(transaction.get("velocity_1h", 0) or 0)
    if amount >= 10000:
        score += 0.30
    if velocity >= 5:
        score += 0.25
    if str(transaction.get("receiver_country", "")).upper() in {"IR", "KP", "RU", "SY"}:
        score += 0.25
    if transaction.get("new_device"):
        score += 0.10
    score = min(score, 0.99)
    level = "HIGH" if score >= 0.85 else "MEDIUM" if score >= 0.65 else "LOW"
    action = "BLOCK_AND_REVIEW" if level == "HIGH" else "STEP_UP_REVIEW" if level == "MEDIUM" else "ALLOW"
    return {
        "transaction_id": transaction.get("transaction_id"),
        "risk_score": round(score, 2),
        "risk_level": level,
        "recommended_action": action,
        "model_version": transaction.get("model_version", "aml-enterprise-default-risk-model:v1"),
        "explanations": [
            reason for cond, reason in [
                (amount >= 10000, "high_amount"),
                (velocity >= 5, "high_velocity_1h"),
                (str(transaction.get("receiver_country", "")).upper() in {"IR", "KP", "RU", "SY"}, "high_risk_country"),
                (bool(transaction.get("new_device")), "new_device"),
            ] if cond
        ],
        "audit_required": True,
    }


class TransactionRiskScoringAgent:
    name = "transaction-risk-scoring-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        scoring = service_profile.get("risk_scoring", {}) or {}
        if not scoring.get("enabled"):
            return []
        checks = [
            ("model_mapping", "risk-missing-model-mapping", "risk model mapping missing", "configured"),
            ("risk_score_response", "risk-missing-score-response", "risk score response missing", True),
            ("explainability", "risk-missing-explainability", "risk explanation/top features missing", True),
            ("audit_log", "risk-missing-audit-log", "risk scoring audit log missing", True),
            ("case_management_handoff", "risk-missing-case-handoff", "case management handoff missing", True),
            ("latency_slo_ms", "risk-missing-latency-slo", "risk scoring latency SLO missing", "<=150ms"),
        ]
        findings: List[Finding] = []
        for key, fid, title, expected in checks:
            if scoring.get(key) in (None, False, ""):
                findings.append(Finding(
                    id=fid,
                    title=f"Transaction risk scoring gap: {title}",
                    category="risk_scoring",
                    severity="P1",
                    evidence=[Evidence("service_profile", f"risk_scoring.{key}", str(scoring.get(key)), str(expected), collector=self.name)],
                    impact={
                        "user_impact": "High-risk transactions may not be scored or explained consistently.",
                        "business_impact": "Fraud/AML controls and auditability may be weakened.",
                        "technical_impact": "Risk scoring lifecycle is not fully declared for this service.",
                    },
                    recommendation={"summary": f"Configure risk_scoring.{key} using the AML/MLOps golden path.", "remediation_type": "approval_required"},
                    confidence={"score": 0.88, "explanation": "Risk scoring profile is missing a mandatory AML control."},
                ))
        return findings
