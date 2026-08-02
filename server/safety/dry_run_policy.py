from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ApprovalRequired(Exception):
    pass


@dataclass
class DryRunDecision:
    mode: str
    execution_allowed: bool
    approval_required: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "execution_allowed": self.execution_allowed,
            "approval_required": self.approval_required,
            "reason": self.reason,
        }


@dataclass
class DryRunPolicy:
    def enforce(self, *, dry_run: bool = True, approved: bool = False, risk: str = "medium") -> DryRunDecision:
        risk = risk.lower()
        if dry_run:
            return DryRunDecision("recommendation_only", False, risk in {"medium", "high", "critical"}, "dry_run_enabled")
        if risk == "critical":
            return DryRunDecision("manual_only", False, True, "critical_risk_actions_are_manual_only")
        if not approved:
            return DryRunDecision("approval_required", False, True, "approval_required_before_execution")
        return DryRunDecision("execution_allowed", True, False, "approved_and_policy_passed")
