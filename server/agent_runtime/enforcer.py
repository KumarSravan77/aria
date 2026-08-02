from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from server.agent_runtime.contract import AgentRuntimeContract
try:
    from server.safety.mutation_guard import MutationGuard
except Exception:
    MutationGuard = None


@dataclass
class AgentRuntimeEnforcer:
    contract: AgentRuntimeContract = field(default_factory=AgentRuntimeContract)

    def validate_action(self, action: str, *, tool: str | None = None, approved: bool = False, approval_id: str | None = None, actor_id: str | None = None, before_state: dict[str, Any] | None = None, rollback_plan: dict[str, Any] | None = None) -> dict[str, Any]:
        violations = []
        action_norm = action.lower().replace(" ", "_")
        tool = tool or action_norm

        if actor_id is None:
            violations.append("missing_actor_identity")

        if action_norm in self.contract.permissions.forbidden_actions:
            violations.append("forbidden_action")

        if tool not in self.contract.permissions.allowed_tools and action_norm not in self.contract.permissions.approval_required_actions:
            violations.append("tool_not_allowed")

        requires_approval = action_norm in self.contract.permissions.approval_required_actions
        if requires_approval and not approved:
            violations.append("approval_required")
        if requires_approval and not approval_id:
            violations.append("approval_id_required")

        is_write = requires_approval or action_norm.startswith(("update", "delete", "patch", "apply", "sync", "scale", "restart"))
        if is_write:
            if before_state is None:
                violations.append("before_state_required")
            if rollback_plan is None:
                violations.append("rollback_plan_required")

        if MutationGuard is not None:
            scan = MutationGuard().scan_text(action)
            if not scan.get("safe", True):
                violations.append("dangerous_mutation_pattern")

        return {
            "runtime_decision_id": str(uuid.uuid4()),
            "allowed": not violations,
            "violations": violations,
            "requires_approval": requires_approval,
            "action": action,
            "tool": tool,
            "actor_id": actor_id,
            "runtime_contract": "identity+permission+tool+memory+observability+evaluation+reversibility",
        }

    def validate_tool_call(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self.contract.permissions.allowed_tools:
            return {"allowed": False, "violations": ["tool_not_allowed"], "tool": tool_name}
        return {"allowed": True, "violations": [], "tool": tool_name, "payload_keys": sorted(payload.keys())}
