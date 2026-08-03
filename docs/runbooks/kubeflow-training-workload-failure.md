---
id: RB-ML-001
title: Kubeflow training workload failure
service: ml-platform
domain: machine-learning-platform
team: ml-platform
environment: all
severity: SEV2
doc_type: runbook
version: 1.0.0
last_reviewed: 2026-08-03
review_cycle_days: 90
tags: [kubeflow, trainjob, gpu, scheduling, headlamp]
sources: [kubernetes, prometheus, loki, tempo, headlamp]
required_permissions: [runbook:read, telemetry:read, kubernetes:read, kubeflow:read]
---

# Kubeflow training workload failure

## Purpose and scope
Diagnose failed or stalled Kubeflow TrainJob, Katib, Notebook, Pipeline, and Spark workloads without allowing the AI investigator to mutate the cluster.

## Customer and business impact
Training or experimentation is delayed, model freshness can breach its objective, and downstream inference releases may remain blocked. Never trade data integrity or model-governance controls for recovery speed.

## Preconditions and access
Use a ReBAC-authorized identity with read access to the affected namespace, Kubeflow custom resources, Pods, events, approved telemetry, and this runbook. Do not retrieve Secret values, dataset contents, model inputs, or unredacted environment values.

## Detection signals
| Signal | Source/query | Threshold | Meaning |
|---|---|---|---|
| Failed condition | Kubeflow resource status | `True` | Controller reports terminal failure |
| Unschedulable worker | Kubernetes events | sustained for 10 minutes | Capacity, quota, selector, taint or GPU constraint |
| Worker restarts | Prometheus/Kubernetes | increasing | Runtime, memory or application failure |
| Missing progress | Kubeflow status and workload metric | no transition for expected duration | Stalled control loop or worker |

## Evidence collection
| Step | Risk | Evidence | Expected result |
|---|---|---|---|
| 1 | read-only | Capture resource API version, UID, generation and status conditions | Identify controller-reported state |
| 2 | read-only | Inspect related Pod conditions and namespace events | Find the first Kubernetes failure |
| 3 | read-only | Inspect requests, limits, PVC state, selectors and tolerations | Confirm scheduling or storage constraints |
| 4 | read-only | Correlate authorized Prometheus, Loki and Tempo evidence in the incident window | Confirm workload or dependency failure |
| 5 | read-only | Open the resource in Headlamp and inspect owner-reference edges | Validate the custom-resource-to-Pod chain |

## Decision tree
```text
Resource unavailable?
├─ Yes: restore authorized API visibility; make no workload change
└─ No
   ├─ Image pull failure: validate immutable image reference and registry access
   ├─ OOMKilled: compare measured memory with request and limit
   ├─ PVC pending: validate storage class, quota and capacity
   ├─ GPU unschedulable: validate capacity, quota, selectors and tolerations
   ├─ Runtime reference invalid: validate installed TrainingRuntime
   └─ Worker failed: inspect the first failed worker and correlated telemetry
```

## Mitigation
- **Read-only:** Pause downstream promotion while evidence is incomplete.
- **Approval-required:** Correct resources, runtime references, storage configuration or scheduling policy through a reviewed GitOps change.
- **Approval-required:** Retry or suspend a production training workload only after checking checkpoint and duplicate-execution behavior.
- **Forbidden-for-AI:** Delete training data, PVCs, namespaces, model artifacts, experiments, or governance evidence.

## Recovery validation
- The custom resource reports the expected progressing or succeeded condition.
- Required workers are ready and no new warning events appear during the stability window.
- Training progress and resource metrics recover without repeated restarts.
- Output artifacts pass integrity, lineage and model-governance checks.
- Downstream promotion remains gated until validation is recorded.

## Escalation
Escalate to the ML platform owner for controller/runtime failures, the Kubernetes platform owner for scheduling/storage failures, and the model owner for code or data-contract failures. Include resource UID and generation, UTC window, conditions, events, image digest, telemetry links and attempted mitigations.

## Rollback
Revert only through the approved GitOps or ML pipeline workflow. Preserve checkpoints and artifacts until integrity is confirmed. AI must not execute an imperative production rollback.

## Evidence and audit record
Record incident ID, resource identity, namespace, API version, UTC window, Headlamp link, queries, image digest, Git revision, runbook version, approval identity, proposed change, result and validation window. Redact sensitive workload data.

## Related resources
- Headlamp Kubeflow plugin: https://github.com/headlamp-k8s/plugins/tree/main/kubeflow
- Architecture: `docs/architecture/KUBEFLOW_HEADLAMP_OPERATIONS.md`
- Scenario: `specs/golden-scenarios/kubeflow-training-failure.yaml`

