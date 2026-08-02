# ARIA CI/CD and AI Issue Response Platform

ARIA now includes two additional self-service platform capabilities:

1. **Golden-path CI/CD generation** for onboarded services.
2. **Event-driven AI issue response** when a pipeline, deployment, SLO, runtime, security, or Terraform drift issue happens.

## CI/CD Golden Path

The CI/CD generator creates a provider-neutral pipeline plan and starter templates for GitHub Actions or Jenkins/CloudBees. The generated pipeline includes:

- service discovery
- build
- unit tests
- quality checks
- secrets scan
- SAST/SCA
- container scan
- SBOM/provenance
- policy-as-code validation
- deployment with rollback guard
- post-deployment SLO check
- ARIA post-deploy AI review

API:

```text
POST /aria/platform/cicd/generate
```

Example request:

```json
{
  "service_id": "payments-api",
  "language": "java",
  "cicd_provider": "github-actions",
  "deployment_target": "kubernetes",
  "service_profile": {
    "tier": "tier1",
    "compliance": "pci"
  }
}
```

## AI Issue Response Agent

The AI Issue Response Agent is the event-driven runtime agent. It is triggered by:

- `pipeline_failure`
- `deployment_failure`
- `slo_burn`
- `runtime_alert`
- `security_alert`
- `terraform_drift`

It selects the right specialist agents, creates triage steps, recommends safe actions, and marks whether approval or rollback is required.

API:

```text
POST /aria/platform/issues/analyze
```

The agent remains safe-by-default. It does not mutate production systems directly. It produces a plan with dry-run, approval, rollback, and investigation guidance.

## Correct Responsibility Split

| Capability | Owner |
|---|---|
| Service onboarding | Onboarding Agent |
| CI/CD generation | CI/CD Pipeline Generator |
| Operational readiness | AI Service Review Agent |
| Live incident/pipeline/deploy response | AI Issue Response Agent |
| Terraform drift | Independent Terraform Drift Agent |
| Remediation PR plan | PR Engine + Approval Workflow |

## Event Flow

```text
Pipeline / Alert / SLO / Deployment Event
        ↓
AI Issue Response Agent
        ↓
Classify issue type and severity
        ↓
Run relevant specialist agents
        ↓
Generate triage plan
        ↓
Recommend rollback / PR / mitigation / investigation
        ↓
Require approval for risky actions
```

## Why this matters

This turns ARIA from a static review framework into an active AI DevOps platform. It can standardize how services are built, deployed, reviewed, and investigated when failures happen.
