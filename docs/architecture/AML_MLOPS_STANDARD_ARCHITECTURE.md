# AML/Fraud Data Engineering + MLOps Standard Architecture

This ARIA project treats AML/Fraud workloads as standard production Kubernetes services with additional data, ML, and compliance governance.

## Standard flow

```text
GitHub
  -> GitHub Actions CI
  -> container registry + MLflow model registry
  -> GitOps repo
  -> ArgoCD
  -> Kubernetes + Istio
  -> Observability stack
  -> ARIA AI Service Review / DevOps / MLOps agents
```

## Required platform capabilities

The `python-aml-mlops` golden path requires:

- Kubernetes standards
- GitOps standards
- CI/CD standards
- Service mesh standards
- Observability standards
- Reliability/SLO standards
- Data pipeline standards
- Model governance standards

## Istio responsibilities

Istio is used for:

- strict mTLS
- service-to-service authorization
- retries and timeouts
- canary model rollout
- outlier detection
- traffic splitting
- mesh telemetry

## ArgoCD responsibilities

ArgoCD is used for:

- GitOps deployment
- desired-state reconciliation
- rollback through Git history/revision history
- self-healing of Kubernetes state

## ARIA responsibilities

ARIA evaluates the AML service through the same platform standards used for other Kubernetes applications, then adds extra controls for FINTRAC, PII, data quality, model drift, explainability, retraining, and audit trails.
