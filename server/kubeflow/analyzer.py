from __future__ import annotations

from typing import Any


class KubeflowIncidentAnalyzer:
    """Deterministic analysis of Kubeflow resource and Pod evidence."""

    FAILURE_RULES = (
        ("ImagePullBackOff", ("imagepullbackoff", "errimagepull"), "Verify the image reference and registry access."),
        ("OOMKilled", ("oomkilled", "out of memory"), "Compare memory use with requests and limits."),
        ("PVCBinding", ("unbound immediate persistentvolumeclaims", "persistentvolumeclaim", "pvc pending"), "Inspect PVC events and storage-class capacity."),
        ("GPUScheduling", ("insufficient nvidia.com/gpu", "gpu unavailable", "unschedulable"), "Inspect GPU capacity, quota, selectors, taints and tolerations."),
        ("RuntimeReference", ("trainingruntime", "runtime not found", "invalid runtime"), "Verify the TrainJob runtime reference and installed runtime."),
        ("WorkloadFailed", ("failed", "error", "trial failed"), "Inspect the first failed worker, its events and correlated telemetry."),
        ("WorkloadStalled", ("pending", "stalled", "running too long"), "Compare current state with the last transition and expected duration."),
    )

    def analyze(self, evidence: dict[str, Any], incident: dict[str, Any]) -> dict[str, Any]:
        resource = evidence.get("resource", {}) or {}
        status = resource.get("status", {}) or {}
        text = " ".join(
            str(value).lower()
            for value in (status, incident.get("signals", []), incident.get("symptoms", []), incident.get("summary", ""))
        )
        failure_mode = "GeneralKubeflow"
        recommendation = "Collect resource conditions, related Pod events and telemetry before proposing a change."
        for mode, tokens, action in self.FAILURE_RULES:
            if any(token in text for token in tokens):
                failure_mode = mode
                recommendation = action
                break
        available = bool(evidence.get("available"))
        return {
            "available": available,
            "failure_mode": failure_mode if available else "EvidenceUnavailable",
            "confidence": "high" if available and failure_mode != "GeneralKubeflow" else "low",
            "observations": self._conditions(status),
            "recommendations": [
                recommendation if available else "Restore authorized Kubernetes API access before diagnosing or changing the workload.",
                "Use Headlamp to inspect the custom resource and its Kubernetes ownership graph.",
                "Keep every workload mutation behind policy, approval, audit and recovery validation.",
            ],
        }

    @staticmethod
    def _conditions(status: dict[str, Any]) -> list[dict[str, Any]]:
        conditions = status.get("conditions", []) if isinstance(status, dict) else []
        return [
            {
                "type": item.get("type"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "message": item.get("message"),
            }
            for item in conditions
            if isinstance(item, dict)
        ]

