# Kubernetes-Native Platform Tooling

This folder contains the optional/enterprise Kubernetes tooling layer for ARIA. The goal is not to install every tool by default, but to document and provide safe manifests for the capabilities used by a modern AI-native SRE platform.

## Default implementation stack

| Capability | Primary tool | Purpose |
|---|---|---|
| GitOps | Argo CD | Declarative deployment and sync |
| Canary / blue-green | Argo Rollouts | Progressive delivery and rollback |
| Service mesh | Istio | Traffic splitting, mTLS, fault injection, telemetry |
| Packaging | Helm | Application packaging |
| Environment overlays | Kustomize | dev/stage/prod customization |
| Metrics | Prometheus + Thanos | local metrics + long-term/multi-cluster metrics |
| Pod autoscaling | HPA + KEDA + VPA | horizontal, event-driven, and vertical recommendations |
| Node autoscaling | Karpenter, Cluster Autoscaler option | modern and legacy node autoscaling |
| Policy-as-code | Kyverno | Kubernetes guardrails and mutation/validation policies |
| Admission policies | OPA Gatekeeper | constraint-based admission control |
| Runtime security | Falco | runtime threat detection |
| Scanning | Trivy + Kubescape | image/IaC scanning and cluster posture |
| TLS automation | cert-manager | certificates and issuers |
| Cluster lifecycle | Cluster API, kOps, Rancher | cluster provisioning and multi-cluster management |

## Safety principle

AI agents can recommend a rollout, policy change, or remediation, but real changes must still pass:

```text
ReBAC → policy validation → approval → audit → async executor
```

Do not let an LLM directly run `kubectl`, Argo CD sync, or policy changes.
