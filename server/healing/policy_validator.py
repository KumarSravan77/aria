from __future__ import annotations
from pathlib import Path
import yaml

PRIVILEGED_ROLES = {"sre", "platform-admin", "incident-commander"}
PROD_APPROVAL_ACTIONS = {"scale_deployment", "restart_pod", "restart_deployment", "rollback_deployment"}

class PolicyValidator:
    def __init__(self, policy_path: str | Path):
        self.policy_path = Path(policy_path)
        with self.policy_path.open("r", encoding="utf-8") as f:
            self.policy = yaml.safe_load(f) or {}

    def validate(self, request: dict) -> dict:
        action = request.get("action")
        env = (request.get("environment") or "dev").lower()
        user = request.get("user") or {}
        role = (user.get("role") if isinstance(user, dict) else getattr(user, "role", None)) or "unknown"
        team = (user.get("team") if isinstance(user, dict) else getattr(user, "team", None)) or "unknown"

        allowed = set(self.policy.get("allowed_actions", []))
        restricted = set(self.policy.get("restricted_actions", []))
        approval = set(self.policy.get("require_approval", []))
        privileged_roles = set(self.policy.get("privileged_roles", list(PRIVILEGED_ROLES)))

        if action in restricted:
            return {"allowed": False, "reason": f"{action} is restricted", "requires_approval": False}
        if action not in allowed:
            return {"allowed": False, "reason": f"{action} is not in allowed_actions", "requires_approval": False}
        if role not in privileged_roles:
            return {"allowed": False, "reason": f"role {role} is not allowed to run healing actions", "requires_approval": False}

        is_prod = env in {"prod", "production"}
        requires_approval = action in approval or (is_prod and action in PROD_APPROVAL_ACTIONS)
        return {
            "allowed": True,
            "reason": "action allowed by policy",
            "requires_approval": requires_approval,
            "actor_role": role,
            "actor_team": team,
        }
