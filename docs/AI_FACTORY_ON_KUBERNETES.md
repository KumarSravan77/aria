# ARIA AI Factory on Kubernetes

This portfolio project implements the control-plane slice of the CNCF AI Factory architecture: multiple teams draw from governed accelerator capacity for training, fine-tuning, evaluation, and inference without sharing authority or bypassing operational controls.

Reference: [Building an AI factory on Kubernetes](https://www.cncf.io/blog/2026/08/27/building-an-ai-factory-on-kubernetes/), CNCF, August 27, 2026.

## Demonstrated architecture

```text
OIDC identity + ARIA ReBAC
          |
          v
Tenant API / workload planner ----> GitOps / Argo CD
          |                              |
          v                              v
Kueue admission + quota --------> tenant namespaces
          |                       /       |       \
          v                      /        |        \
GPU pool: whole GPU / MIG ------+   training   evaluation
          |                              |
          v                              v
KServe + vLLM <---- Envoy AI Gateway   model registry
          |
          v
OTel + Prometheus + DCGM + Grafana + OpenCost
          |
          v
health evidence -> approval-gated cordon/drain -> validation
```

## What runs without a GPU

- The ARIA `/ai-factory/plan` API produces deterministic placement, isolation, scheduling, evidence, and safety decisions.
- The `/ai-factory/capacity` API calculates healthy and available GPU capacity from inventory evidence.
- `platform/ai-factory/base` renders two isolated tenants with resource quotas, restricted Pod Security, default-deny networking, and non-mounted service-account tokens.
- Tests verify that untrusted tenants receive whole-GPU/dedicated-node recommendations and that remediation remains approval-gated.

## NVIDIA production overlay

The production manifests demonstrate:

- Kueue `ClusterQueue`, `LocalQueue`, and GPU resource flavor.
- KServe `InferenceService` backed by vLLM.
- DCGM exporter discovery through `ServiceMonitor`.
- Kyverno labels required for tenant attribution and GPU cost allocation.

Apply these only after installing and validating the corresponding CRDs and operators. Pin images by digest in a real environment.

## Honest capability boundary

| Layer | Portfolio evidence | Current status |
|---|---|---|
| Cluster lifecycle | Existing Cluster API, GitOps and Argo CD assets | Implemented pattern |
| Tenant isolation | Namespaces, quotas, Pod Security, default-deny network | Runnable base |
| GPU scheduling | Kueue quotas and deterministic planner | Declarative overlay |
| Partitioning | Whole-GPU/MIG/time-slicing policy decision | Requires compatible GPU |
| Training | Kubeflow operations and LoRA/QLoRA pipeline | Local smoke verified; distributed GPU pending |
| Inference | KServe, vLLM and Envoy AI Gateway | Declarative GPU overlay |
| Observability | OTel, Prometheus, Grafana, Tempo/Loki, DCGM contract | Platform implemented; GPU metrics need hardware |
| Reliability | Health inventory and governed remediation path | Advisory/approval-gated |
| Chargeback | Tenant attribution and OpenCost integration | Contract/partial |
| Bare metal/RDMA | Architecture and integration points | Not locally implemented |

The project does not claim that a laptop is a production GPU cloud. It proves the API, policy, tenancy, workload, observability, and recovery contracts locally, then supplies explicit hardware-dependent overlays for an NVIDIA Kubernetes environment.

## Validation

```bash
make ai-factory-validate
make ai-factory-test
```

Production acceptance additionally requires GPU Operator/NFD inventory, DCGM health, NCCL topology and bandwidth tests, queue fairness tests, tenant penetration tests, inference load tests, failure injection, and chargeback reconciliation.

## Interview demonstration

1. Submit an internal 10 GiB fine-tuning request and explain why the planner selects MIG within one trust domain.
2. Submit an untrusted inference request and show the whole-GPU plus dedicated-node recommendation.
3. Render the two-tenant base and identify quota, network, Pod Security, and identity boundaries.
4. Walk through Kueue admission into KServe/vLLM and trace tenant GPU-seconds to OpenCost.
5. Mark one GPU node unhealthy and show why available capacity excludes it.
6. Explain why ARIA proposes but does not autonomously drain the node.
