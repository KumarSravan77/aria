# Kubeflow and Headlamp operations integration

## Outcome

Headlamp is the operator-facing Kubernetes UI. Its Kubeflow plugin discovers installed Kubeflow API groups and visualizes their resources and ownership relationships. ARIA remains the governed investigation plane: it reads the same custom resources, correlates telemetry and runbooks, explains likely failure modes, and produces recommendations without executing them.

```text
Kubeflow and Spark CRDs ─┬─> Headlamp Kubeflow plugin ─> operator view
                         └─> ARIA read-only client
                                  ├─> deterministic analyzer
                                  ├─> Prometheus/Loki/Tempo correlation
                                  ├─> RAG runbook
                                  └─> governed recommendation
```

## Delivery plan

1. **Evidence contract — complete:** Read Notebook, Pipeline, Katib, Trainer and Spark resources through the Kubernetes Custom Objects API; return only operational metadata, summarized spec fields and status.
2. **Deterministic investigation — complete:** Classify image, memory, storage, GPU scheduling, runtime-reference, failure and stalled-workload scenarios.
3. **API and authorization — complete:** Expose `/kubeflow/resources` and `/kubeflow/investigate`; require authentication and namespace ReBAC.
4. **Knowledge and demonstration — complete:** Add a RAG-ready runbook, example payload and golden scenario.
5. **Headlamp operator experience — integration boundary:** Install Headlamp and the upstream Apache-2.0 Kubeflow plugin using the versions approved by the target environment. Set `HEADLAMP_BASE_URL` to add navigation evidence to investigations.
6. **Live validation — environment dependent:** Validate against a CRD-only Kind cluster, then a modular Kubeflow installation. Retain resource snapshots and test evidence before claiming production compatibility.

## Supported APIs

- `kubeflow.org/v1`: Notebook, Profile
- `kubeflow.org/v1alpha1`: PodDefault
- `pipelines.kubeflow.org/v2beta1`: Pipeline, PipelineVersion
- `kubeflow.org/v1beta1`: Experiment, Trial, Suggestion
- `trainer.kubeflow.org/v1alpha1`: TrainJob, TrainingRuntime, ClusterTrainingRuntime
- `sparkoperator.k8s.io/v1beta2`: SparkApplication, ScheduledSparkApplication

Missing CRDs degrade gracefully. ARIA returns `available: false` and does not infer that a resource exists.

## Security boundary

`platform/kubeflow/aria-reader-rbac.yaml` contains only `get`, `list`, and `watch`. ARIA never reads Secret data and removes environment values and detailed workload specifications from its normalized evidence. Any retry, suspension, resource adjustment or GitOps proposal remains behind ReBAC, policy validation, approval, audit and recovery validation.

## Validation

```text
pytest tests/test_kubeflow_operations.py -q
kubectl apply --dry-run=client -f platform/kubeflow/aria-reader-rbac.yaml
```

The second validation requires compatible Kubernetes API discovery. Do not apply the cluster-wide binding without security review.

