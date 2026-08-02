from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedServiceSnapshot:
    """Canonical service snapshot consumed by ARIA service reviews.

    Live connectors should normalize Git, Kubernetes, CI/CD, telemetry, and IaC
    evidence into this model before running the AI Service Review Agent.
    """

    service_id: str
    environment: str = "dev"
    service_profile: Dict[str, Any] = field(default_factory=dict)
    slo_config: Optional[Dict[str, Any]] = None
    telemetry_snapshot: Optional[Dict[str, Any]] = None
    incident_history: List[Dict[str, Any]] = field(default_factory=list)
    latest_drift_summary: Optional[Dict[str, Any]] = None
    source_status: Dict[str, str] = field(default_factory=dict)

    def to_review_request(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "environment": self.environment,
            "service_profile": self.service_profile,
            "slo_config": self.slo_config,
            "telemetry_snapshot": self.telemetry_snapshot,
            "incident_history": self.incident_history,
            "latest_drift_summary": self.latest_drift_summary,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "service_id": self.service_id,
            "environment": self.environment,
            "service_profile": self.service_profile,
            "slo_config": self.slo_config,
            "telemetry_snapshot": self.telemetry_snapshot,
            "incident_history": self.incident_history,
            "latest_drift_summary": self.latest_drift_summary,
            "source_status": self.source_status,
        }
