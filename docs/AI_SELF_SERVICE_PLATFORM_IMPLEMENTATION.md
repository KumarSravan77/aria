# ARIA AI Self-Service DevOps Platform Implementation

ARIA now includes an integrated self-service platform control plane on top of the existing agentic runtime.

## What is implemented

### Self-Service Control Plane

`server/platform/control_plane.py` exposes the main workflow entry points:

- `onboard_service(request)`
- `review_service(request)`
- `run_terraform_drift(terraform_plan, environment)`

### AI Service Review Agent

The AI Service Review Agent now runs specialist agents instead of only local inline checks:

- Reliability Agent
- Kubernetes Standards Agent
- Observability Standards Agent
- OpenTelemetry Guardian Agent
- CI/CD Standards Agent
- Security Governance Agent
- Cost Optimization Agent
- Runbook Quality Agent

It intentionally does **not** run Terraform Drift Agent directly. It only consumes the latest drift summary when one already exists.

### Onboarding Agent

The Onboarding Agent runs the initial Terraform drift baseline, then runs the Service Review Agent and generates self-service golden-path artifacts:

- `kubernetes/helm-values.yaml`
- `cicd/pipeline-template.yaml`
- `observability/otel-collector.yaml`
- `slo/service-slo.yaml`
- `runbooks/operational-runbook.md`

### Terraform Drift Agent

The Terraform Drift Agent remains independent and can be called by:

- onboarding baseline
- scheduled drift checks
- pre-release checks
- audit workflows
- manual on-demand review

### Spec/Harness Development

The spec-driven layer remains in `/specs` and the tests validate behavior through harness-style scenarios.

## Implemented Specialist Agents

| Agent | Path | Purpose |
|---|---|---|
| Kubernetes Standards Agent | `server/platform/kubernetes_standards/agent.py` | Probes, PDB, resources, topology spread |
| Observability Standards Agent | `server/platform/observability_standards/agent.py` | Metrics, logs, traces, dashboards, alerts, correlation IDs |
| OpenTelemetry Guardian Agent | `server/platform/otel_guardian/agent.py` | OTel enablement, service.name, propagation, collector, high-cardinality risk |
| CI/CD Standards Agent | `server/platform/cicd_standards/agent.py` | Build, tests, security scan, SBOM, signing, rollback, safe deployments |
| Security Governance Agent | `server/platform/security_governance/agent.py` | RBAC, NetworkPolicy, security context, secrets, image scan, policy-as-code |
| Cost Optimization Agent | `server/platform/cost_optimization/agent.py` | Owner tags, budget alerts, observability cost/cardinality risk |
| Runbook Quality Agent | `server/platform/runbook_quality/agent.py` | Owner, escalation, dashboards, rollback steps, known failure modes |

## Current maturity

This is a working deterministic platform foundation. It does not yet connect to live GitHub/Jenkins/Kubernetes/Dynatrace/Prometheus/Terraform Cloud APIs. The next layer is live connector implementation.

## Validation

Validated focused platform tests:

```bash
PYTHONPATH=. pytest -q \
  tests/test_agent_runtime_contract.py \
  tests/test_kubernetes_internals.py \
  tests/test_rag_types.py \
  tests/test_spec_driven_service_review.py \
  tests/test_platform_control_plane_integration.py
```

Result:

```text
25 passed
```

Full repository test run still requires optional project dependencies such as SQLAlchemy.
