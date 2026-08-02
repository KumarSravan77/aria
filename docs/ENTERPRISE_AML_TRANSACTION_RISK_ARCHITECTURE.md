# ARIA Enterprise AML/Fraud Transaction Risk Architecture

This module makes AML/Fraud a platform-wide capability instead of an isolated ML service.
Every transaction-producing application publishes governed transaction events to Kafka, the AML feature pipeline enriches them, and the fraud detection engine returns a risk score and decision.

## Runtime flow

```text
Application transaction
  -> transactions.events Kafka topic
  -> AML feature pipeline
  -> Feast feature store
  -> Fraud/AML model served by KServe
  -> transactions.risk-scored Kafka topic
  -> decision/case-management workflow
  -> ARIA monitors SLOs, drift, security, DevSecOps, and incidents
```

## What ARIA enforces per service

- CI/CD: build, test, security scans, SBOM, image signing, rollback.
- DevSecOps: Semgrep/SonarQube, Snyk/Dependabot, Trivy, Gitleaks, Checkov/tfsec, Syft, Cosign, Kyverno/Gatekeeper, Falco.
- Kubernetes: probes, requests/limits, HPA, PDB, network policy, security context.
- Istio: mTLS, retries, timeouts, canary traffic, AuthorizationPolicy, telemetry.
- Observability: OpenTelemetry traces, Prometheus metrics, logs, SLOs, error budgets.
- Data engineering: schema validation, lineage, data quality, idempotency, backfill/replay, pipeline SLA.
- MLOps: MLflow registry, KServe deployment, explainability, model drift, feature drift, retraining trigger.
- AML risk scoring: model mapping, risk score response, explanations, thresholds, audit log, case handoff.

## Example risk response

```json
{
  "transaction_id": "txn-1001",
  "risk_score": 0.92,
  "risk_level": "HIGH",
  "recommended_action": "BLOCK_AND_REVIEW",
  "explanations": ["high_amount", "high_velocity_1h", "high_risk_country"],
  "model_version": "aml-enterprise-default-risk-model:v1",
  "audit_required": true
}
```

This design keeps ARIA aligned with enterprise platform architecture: GitHub Actions for CI, ArgoCD for GitOps CD, Kubernetes + Istio for runtime, OpenTelemetry/Prometheus/Grafana/Dynatrace for observability, Vault/ESO for secrets, and ARIA agents for governance and response.
