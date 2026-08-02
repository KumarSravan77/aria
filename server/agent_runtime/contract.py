from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IdentityContract:
    actor_type: str = "scoped_machine_identity"
    actor_id: str = "aria-agent"
    tenant: str = "enterprise"
    scopes: list[str] = field(default_factory=lambda: ["investigate", "recommend"])


@dataclass
class PermissionContract:
    allowed_tools: list[str] = field(default_factory=lambda: [
        "metrics.query",
        "logs.query",
        "traces.query",
        "rag.retrieve",
        "kubernetes.read",
        "kafka.read",
        "istio.read",
        "gitops.propose_pr",
    ])
    read_scopes: list[str] = field(default_factory=lambda: ["owned_services", "rebac_filtered_runbooks"])
    approval_required_actions: list[str] = field(default_factory=lambda: [
        "kubernetes.scale",
        "kubernetes.restart",
        "argocd.sync",
        "rollout.promote",
        "rollout.abort",
        "gitops.merge",
        "customer_record.change",
    ])
    forbidden_actions: list[str] = field(default_factory=lambda: [
        "delete_namespace",
        "delete_topic",
        "reset_offsets",
        "drop_database",
        "bypass_approval",
        "direct_customer_record_update",
    ])


@dataclass
class ToolContract:
    tool_name: str
    schema: dict[str, Any]
    timeout_seconds: int = 10
    retry_count: int = 0
    failure_mode: str = "degrade_gracefully"
    mutation: bool = False


@dataclass
class MemoryContract:
    allowed_memory_types: list[str] = field(default_factory=lambda: ["incident_summary", "rca", "runbook_signal", "remediation_outcome"])
    ttl_days: int = 180
    pii_allowed: bool = False
    user_inspectable: bool = True
    delete_supported: bool = True


@dataclass
class ObservabilityContract:
    trace_required: bool = True
    audit_required: bool = True
    debug_log_required: bool = True
    token_tracking_required: bool = True
    tool_call_trace_required: bool = True


@dataclass
class EvaluationContract:
    route_score_required: bool = True
    retrieval_score_required: bool = True
    safety_score_required: bool = True
    hallucination_check_required: bool = True
    cost_tracking_required: bool = True


@dataclass
class ReversibilityContract:
    before_state_required: bool = True
    after_state_required: bool = True
    rollback_plan_required: bool = True
    approval_id_required: bool = True
    audit_id_required: bool = True


@dataclass
class AgentRuntimeContract:
    identity: IdentityContract = field(default_factory=IdentityContract)
    permissions: PermissionContract = field(default_factory=PermissionContract)
    tools: dict[str, ToolContract] = field(default_factory=dict)
    memory: MemoryContract = field(default_factory=MemoryContract)
    observability: ObservabilityContract = field(default_factory=ObservabilityContract)
    evaluation: EvaluationContract = field(default_factory=EvaluationContract)
    reversibility: ReversibilityContract = field(default_factory=ReversibilityContract)

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.__dict__,
            "permissions": self.permissions.__dict__,
            "tools": {k: v.__dict__ for k, v in self.tools.items()},
            "memory": self.memory.__dict__,
            "observability": self.observability.__dict__,
            "evaluation": self.evaluation.__dict__,
            "reversibility": self.reversibility.__dict__,
            "runtime_invariant": "No write action without identity, permission, approval, audit, rollback plan and validation.",
        }
