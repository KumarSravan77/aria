# ARIA AI Self-Service DevOps Platform Buildout

ARIA now has a working self-service control-plane foundation for onboarding and reviewing services against platform standards.

## What it does now

1. Builds a normalized service snapshot from self-service inputs.
2. Reads local repository evidence through connector normalizers.
3. Normalizes Kubernetes object snapshots into service-profile signals.
4. Extracts CI/CD governance signals from Jenkins, GitHub Actions, GitLab CI, and Azure DevOps files.
5. Normalizes SLI/SLO telemetry snapshots for reliability review.
6. Runs the AI Service Review Agent across reliability, Kubernetes, observability, OTel, CI/CD, security, cost, and runbook quality.
7. Keeps Terraform Drift Agent independent, but allows onboarding to create an initial IaC baseline.
8. Generates a markdown operational readiness report.
9. Generates dry-run remediation PR plans and approval tickets.

## Main APIs

```text
POST /platform/self-service/snapshot
POST /platform/self-service/onboard
POST /platform/self-service/service-review
POST /platform/self-service/service-review/report
POST /platform/self-service/remediation/pr-plan
POST /platform/self-service/terraform-drift/analyze
POST /platform/self-service/terraform-drift/commands
```

## Correct responsibility split

```text
Onboarding Agent
  - runs initial service discovery
  - creates platform baseline
  - may trigger Terraform Drift Agent once for initial baseline

AI Service Review Agent
  - runs operational readiness review
  - does not run Terraform drift directly
  - consumes latest drift summary if available

Terraform Drift Agent
  - independent on-demand/scheduled/pre-release/audit workflow
  - produces drift summary for review consumption
```

## Production connectors still pending

The current connectors are safe local/read-only normalizers. Real production integrations should plug into the same normalized snapshot contract:

- GitHub/GitLab/Bitbucket API connector
- Jenkins/GitHub Actions/Azure DevOps runtime connector
- Kubernetes API live connector
- Dynatrace metrics/events/SLO connector
- Prometheus/Thanos connector
- Terraform Cloud/Enterprise connector
- ServiceNow/Jira ticket connector
- Slack/Teams approval connector

## Safety model

ARIA keeps remediation in dry-run mode by default. PR plans and approval tickets are generated, but no cloud mutation or Git write happens without an external approved implementation.
