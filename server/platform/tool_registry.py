from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class PlatformTool:
    name: str
    purpose: str
    mode: str
    folder: str
    primary: bool = False

TOOLS = [
    PlatformTool("Argo CD", "GitOps deployment and sync", "active-adapter", "platform/gitops/argocd", True),
    PlatformTool("Argo Rollouts", "Canary and blue-green progressive delivery", "active-adapter", "platform/gitops/rollouts", True),
    PlatformTool("Helm", "Kubernetes packaging", "install-option", "platform/packaging/helm", True),
    PlatformTool("Kustomize", "Environment overlays", "install-option", "platform/packaging/kustomize", True),
    PlatformTool("Istio", "Primary service mesh, traffic splitting, mTLS, telemetry", "install-option", "platform/mesh/istio", True),
    PlatformTool("Prometheus", "Metrics and rollout analysis", "active-adapter", "platform/observability/prometheus", True),
    PlatformTool("Thanos", "Long-term and multi-cluster Prometheus metrics", "install-option", "platform/observability/thanos", True),
    PlatformTool("KEDA", "Event-driven pod autoscaling", "active-adapter", "platform/autoscaling/keda", True),
    PlatformTool("VPA", "Vertical pod autoscaling recommendations", "install-option", "platform/autoscaling/vpa"),
    PlatformTool("Karpenter", "Modern node autoscaling", "install-option", "platform/autoscaling/karpenter", True),
    PlatformTool("Cluster Autoscaler", "Legacy/alternative node autoscaling", "install-option", "platform/autoscaling/cluster_autoscaler"),
    PlatformTool("Falco", "Runtime threat detection", "active-webhook", "platform/security/falco", True),
    PlatformTool("Kyverno", "Kubernetes policy-as-code", "policy-manifests", "platform/security/kyverno", True),
    PlatformTool("OPA Gatekeeper", "Admission policies and constraints", "policy-manifests", "platform/security/gatekeeper"),
    PlatformTool("Trivy", "Container and IaC scanning", "ci-template", "platform/security/trivy", True),
    PlatformTool("Kubescape", "Kubernetes security posture", "ci-template", "platform/security/kubescape", True),
    PlatformTool("cert-manager", "TLS certificate automation", "install-option", "platform/security/cert_manager", True),
    PlatformTool("kOps", "AWS Kubernetes cluster provisioning option", "cluster-lifecycle-option", "platform/cluster_lifecycle/kops"),
    PlatformTool("Rancher", "Multi-cluster management option", "cluster-lifecycle-option", "platform/cluster_lifecycle/rancher"),
    PlatformTool("Cluster API", "Declarative cluster lifecycle option", "cluster-lifecycle-option", "platform/cluster_lifecycle/cluster_api", True),
]

def list_tools() -> dict[str, Any]:
    return {"tools": [tool.__dict__ for tool in TOOLS], "default_stack": [tool.name for tool in TOOLS if tool.primary]}
