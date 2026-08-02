from __future__ import annotations

from typing import Any, Dict, List

from server.platform.spec_harness.models import Evidence, Finding


class EnterpriseEventBusAgent:
    """Checks that transaction-producing apps are wired into the AML/Fraud event bus."""

    name = "enterprise-event-bus-agent"

    def review(self, service_profile: Dict[str, Any]) -> List[Finding]:
        eventing = service_profile.get("eventing", {}) or {}
        produces = bool(eventing.get("publishes_transaction_events"))
        findings: List[Finding] = []
        if not produces:
            return findings
        checks = [
            ("topic", "eventing-missing-topic", "transaction Kafka topic missing", "transactions.events"),
            ("schema", "eventing-missing-schema", "transaction event schema missing", "transaction-event-v1"),
            ("dlq", "eventing-missing-dlq", "dead-letter queue missing", "transactions.events.dlq"),
            ("pii_tokenization", "eventing-missing-pii-tokenization", "PII tokenization missing", True),
            ("lineage_enabled", "eventing-missing-lineage", "lineage metadata missing", True),
            ("consumer_lag_slo", "eventing-missing-lag-slo", "consumer lag SLO missing", True),
            ("idempotency_key", "eventing-missing-idempotency", "idempotency key missing", True),
            ("replay_support", "eventing-missing-replay", "event replay support missing", True),
        ]
        for key, fid, title, expected in checks:
            if eventing.get(key) in (None, False, ""):
                findings.append(Finding(
                    id=fid,
                    title=f"Enterprise event bus gap: {title}",
                    category="eventing",
                    severity="P1" if key in {"topic", "schema", "pii_tokenization"} else "P2",
                    evidence=[Evidence("service_profile", f"eventing.{key}", str(eventing.get(key)), str(expected), collector=self.name)],
                    impact={
                        "user_impact": "Transaction risk scoring may be delayed or unavailable.",
                        "business_impact": "AML/Fraud monitoring coverage may be incomplete.",
                        "technical_impact": "The service is not fully integrated with the governed Kafka event bus.",
                    },
                    recommendation={
                        "summary": f"Configure eventing.{key} for the transactions.events AML/Fraud event stream.",
                        "remediation_type": "auto_fix_candidate",
                    },
                    confidence={"score": 0.86, "explanation": "Transaction producer profile is missing an event bus control."},
                ))
        return findings
