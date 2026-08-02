from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlatformIssueEvent:
    event_type: str
    service_id: str
    environment: str
    severity: str = "P2"
    source: str = "unknown"
    summary: str = ""
    signals: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PlatformIssueEvent":
        return cls(
            event_type=payload.get("event_type", payload.get("type", "unknown")),
            service_id=payload.get("service_id", payload.get("service", "unknown-service")),
            environment=payload.get("environment", "dev"),
            severity=payload.get("severity", "P2"),
            source=payload.get("source", "unknown"),
            summary=payload.get("summary", ""),
            signals=payload.get("signals", {}) or {},
            correlation_id=payload.get("correlation_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class IssueResponsePlan:
    service_id: str
    environment: str
    event_type: str
    severity: str
    incident_mode: str
    agents_to_run: List[str]
    triage_steps: List[str]
    recommended_actions: List[Dict[str, Any]]
    approval_required: bool
    rollback_recommended: bool
    service_review: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "environment": self.environment,
            "event_type": self.event_type,
            "severity": self.severity,
            "incident_mode": self.incident_mode,
            "agents_to_run": self.agents_to_run,
            "triage_steps": self.triage_steps,
            "recommended_actions": self.recommended_actions,
            "approval_required": self.approval_required,
            "rollback_recommended": self.rollback_recommended,
            "service_review": self.service_review,
        }
