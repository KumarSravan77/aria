# ARIA Platform Architecture

```text
Developer / Service Owner
        |
        v
Self-Service Workflow
        |
        +--> Git Repo Connector
        +--> Kubernetes Connector
        +--> CI/CD Connector
        +--> Telemetry Connector
        +--> Terraform Plan Executor
        |
        v
NormalizedServiceContext
        |
        v
ARIA Platform Control Plane
        |
        +--> Onboarding Agent
        |       +--> Terraform Drift Agent
        |       +--> Golden Path Template Generator
        |
        +--> AI Service Review Agent
                +--> Reliability Agent
                +--> Kubernetes Standards Agent
                +--> Observability Standards Agent
                +--> OTel Guardian Agent
                +--> CI/CD Standards Agent
                +--> Security Governance Agent
                +--> Cost Optimization Agent
                +--> Runbook Quality Agent
                +--> latest drift summary only
        |
        v
Reports + Approvals + PR Candidates
```

## Important boundary

Terraform Drift Agent is not executed by every service review. It is independent and can run during onboarding, schedule, audit, or pre-release workflows. The Service Review Agent only consumes the latest drift summary if available.
