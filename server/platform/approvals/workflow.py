from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class ApprovalTicket:
    id: str
    service_id: str
    environment: str
    reason: str
    risk_level: str
    approver_role: str
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


class ApprovalWorkflow:
    """In-memory approval workflow skeleton for safe remediation."""

    def create_from_review(self, review: Dict[str, Any]) -> List[Dict[str, Any]]:
        tickets: List[ApprovalTicket] = []
        for idx, approval in enumerate(review.get("approval_required_actions", [])):
            tickets.append(ApprovalTicket(
                id=f"approval-{review.get('service_id')}-{idx}",
                service_id=review.get("service_id", "unknown"),
                environment=review.get("environment", "unknown"),
                reason=approval.get("reason", "Approval required"),
                risk_level=approval.get("risk_level", "medium"),
                approver_role=approval.get("approver_role", "service-owner"),
            ))
        return [ticket.to_dict() for ticket in tickets]
