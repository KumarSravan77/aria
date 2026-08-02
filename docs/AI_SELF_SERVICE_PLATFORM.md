# ARIA AI Self-Service DevOps Platform

ARIA is now structured as a self-service Internal Developer Platform foundation. It accepts normalized inputs from Git repositories, Kubernetes manifests/API objects, CI/CD pipelines, telemetry snapshots, and Terraform plans, then produces onboarding baselines, operational readiness reviews, approval-gated remediation candidates, and markdown reports.

## What it does now

1. **Builds a normalized service context** from repo, Kubernetes, CI/CD, telemetry, and Terraform inputs.
2. **Runs self-service onboarding** to create golden-path artifacts for Kubernetes, CI/CD, observability, SLOs, and runbooks.
3. **Runs AI Service Review** across reliability, Kubernetes, observability, OpenTelemetry, CI/CD, security, cost, runbook quality, and latest Terraform drift summary.
4. **Generates operational readiness reports** in markdown.
5. **Creates approval requests** for risky remediation items.
6. **Creates PR candidate metadata** for future GitHub/GitLab integration.
7. **Keeps Terraform Drift independent** while allowing onboarding to create an initial IaC baseline.

## Control plane flow

```text
Self-Service Request
  -> Connector Normalization
  -> Onboarding Agent
  -> Terraform Drift Baseline
  -> AI Service Review Agent
  -> Markdown Report
  -> Approval Requests
  -> PR Candidate Metadata
```

## Connector contracts

- `GitRepoConnector`: detects language, CI/CD files, Kubernetes files, Terraform files, and OTel hints.
- `KubernetesConnector`: normalizes Kubernetes resources into probes/resources/HPA/PDB standards signals.
- `CICDConnector`: normalizes pipeline stages into security, SBOM, canary, rollback, and deploy signals.
- `TelemetryConnector`: normalizes telemetry into SLI/SLO fields such as availability, p95 latency, error rate, burn rate, and error budget remaining.
- `TerraformPlanExecutor`: parses Terraform JSON plans or provides a safe execution foundation for `terraform init/plan/show`.

## Production integrations still to wire

- GitHub/GitLab PR creation API
- Jenkins/Azure DevOps/GitHub Actions live pipeline discovery
- Kubernetes live API collector
- Dynatrace/Prometheus telemetry collectors
- Terraform Cloud/Spacelift/Atlantis integration
- Approval integration with Jira/ServiceNow/Slack/PagerDuty
- UI developer portal
