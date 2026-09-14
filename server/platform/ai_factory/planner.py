from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WorkloadRequest:
    tenant: str
    workload_type: str
    trust_level: str
    gpu_count: int = 1
    gpu_memory_gib: int | None = None
    priority: str = "standard"
    distributed: bool = False


class AiFactoryPlanner:
    """Deterministic advisory planner; it never allocates or drains hardware."""

    workload_types = {"training", "fine-tuning", "inference", "evaluation"}
    trust_levels = {"trusted", "internal", "untrusted"}

    def plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = WorkloadRequest(**payload)
        self._validate(request)
        strict_boundary = request.trust_level == "untrusted"
        allocation = "whole-gpu" if strict_boundary else (
            "mig" if request.gpu_memory_gib and request.gpu_memory_gib <= 20 else "time-slicing"
        )
        scheduler = "kueue+volcano" if request.distributed or request.workload_type == "training" else "kueue"
        serving = "kserve+vllm" if request.workload_type == "inference" else None
        return {
            "request": asdict(request),
            "decision": {
                "tenant_boundary": "dedicated-node-pool" if strict_boundary else "tenant-namespace",
                "allocation": allocation,
                "scheduler": scheduler,
                "serving": serving,
                "network": "cilium-default-deny",
                "storage": "tenant-scoped-csi",
                "identity": "oidc-rbac",
            },
            "required_evidence": [
                "gpu_inventory", "gpu_health", "queue_admission", "quota", "image_signature",
                "network_policy", "dataset_lineage", "trace_id", "tenant_gpu_seconds",
            ],
            "safety": {
                "advisory_only": True,
                "automatic_node_drain": False,
                "remediation_path": "detect -> cordon proposal -> approval -> deterministic drain -> validation",
            },
        }

    def capacity_summary(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        total = sum(int(node.get("gpu_count", 0)) for node in nodes)
        healthy = sum(int(node.get("gpu_count", 0)) for node in nodes if node.get("healthy", False))
        allocated = sum(int(node.get("allocated_gpus", 0)) for node in nodes)
        return {
            "gpu_total": total,
            "gpu_healthy": healthy,
            "gpu_allocated": allocated,
            "gpu_available": max(healthy - allocated, 0),
            "utilization": round(allocated / max(healthy, 1), 4),
            "unhealthy_nodes": [node.get("name") for node in nodes if not node.get("healthy", False)],
        }

    def _validate(self, request: WorkloadRequest) -> None:
        if not request.tenant.strip():
            raise ValueError("tenant is required")
        if request.workload_type not in self.workload_types:
            raise ValueError("unsupported workload_type")
        if request.trust_level not in self.trust_levels:
            raise ValueError("unsupported trust_level")
        if request.gpu_count < 1 or request.gpu_count > 64:
            raise ValueError("gpu_count must be between 1 and 64")
