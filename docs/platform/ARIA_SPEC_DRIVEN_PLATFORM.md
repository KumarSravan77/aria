# ARIA Spec-Driven AI Cloud Platform

ARIA now has a harness-driven, spec-driven development layer for building the self-service AI Cloud Platform.

## Main platform agents

- AI Service Review Agent
- Onboarding Agent
- Terraform Drift Agent
- Reliability Agent
- OpenTelemetry Guardian Agent
- Kubernetes Standards Agent
- CI/CD Standards Agent

## Design boundary

Terraform Drift Agent is independent. It is triggered by onboarding, schedule, pre-release, audit, or on-demand workflows. The AI Service Review Agent does not run drift directly; it only consumes the latest drift summary if available.

## Development lifecycle

1. Write the agent spec in `specs/agents`.
2. Define or reuse contracts in `specs/contracts`.
3. Add a golden scenario in `specs/golden-scenarios`.
4. Add a harness in `specs/harness`.
5. Add deterministic fixtures and tests.
6. Implement the agent/check.
7. Validate the output against the finding, score, remediation, and approval contracts.
8. Update platform docs and runbooks.

## Operational readiness review

The AI Service Review Agent produces:

- executive summary
- operational readiness score
- reliability score
- Kubernetes maturity score
- observability maturity score
- CI/CD maturity score
- P0/P1/P2 findings
- remediation backlog
- approval-required actions
- drift status if a previous drift scan exists

## Reliability intelligence

The Reliability Agent evaluates:

- availability SLO
- latency SLO
- error budget remaining
- burn rate
- incident and alert quality inputs
- approval gates for high-risk reliability findings

## Self-service onboarding

The Onboarding Agent can create a baseline for a service by running standards checks and Terraform drift baseline creation, then generating initial templates for Kubernetes, CI/CD, OTel, SLO, and runbook standards.
