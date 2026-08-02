from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

Severity = Literal["P0", "P1", "P2", "P3", "INFO"]
Category = Literal[
    "reliability", "kubernetes", "observability", "security",
    "cicd", "cost", "terraform", "runbook", "onboarding",
    "data_pipeline", "mlops", "eventing", "risk_scoring", "devsecops"
]


@dataclass
class Evidence:
    source: str
    path: str
    observed: str
    expected: str
    timestamp: Optional[str] = None
    collector: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "observed": self.observed,
            "expected": self.expected,
            "timestamp": self.timestamp,
            "collector": self.collector,
        }


@dataclass
class Finding:
    id: str
    title: str
    category: Category
    severity: Severity
    evidence: List[Evidence]
    impact: Dict[str, str]
    recommendation: Dict[str, str]
    confidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "evidence": [item.to_dict() for item in self.evidence],
            "impact": self.impact,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
        }


@dataclass
class Score:
    name: str
    grade: Literal["A", "B", "C", "D", "F"]
    numeric_score: float
    rationale: str
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class Approval:
    required: bool
    reason: str
    approver_role: str = "service-owner"
    risk_level: Literal["low", "medium", "high", "critical"] = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class Remediation:
    id: str
    finding_id: str
    type: Literal["manual", "patch", "pull_request", "runbook", "rollback", "scale", "config_change"]
    safety: Dict[str, bool]
    steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()
