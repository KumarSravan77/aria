# ARIA Secrets Governance

ARIA includes a secret governance layer for enterprise AI DevOps and SRE workflows.

## Core rules

- ARIA must never store or print raw secrets.
- CI/CD should use OIDC federation to Vault, AWS Secrets Manager, or Azure Key Vault.
- Kubernetes workloads should prefer External Secrets Operator or Vault Agent Injector.
- Logs, runbooks, Slack exports, incident notes, and CI outputs must be redacted before RAG indexing.
- Secret rotation is dry-run by default and requires approval for production mutation.

## Main components

- `SecretBroker`: issues metadata/lease references for Vault-style short-lived credentials.
- `SecretGovernanceAgent`: detects hardcoded secrets, static CI secrets, and K8s secret exposure risks.
- `SecretRedactor`: redacts common secrets before prompts, reports, and RAG ingestion.
- `/aria/platform/secrets/*`: API endpoints for lease, review, and RAG sanitization.

## Recommended Kubernetes pattern

Vault → External Secrets Operator → Kubernetes Secret → workload.

## Recommended CI/CD pattern

GitHub Actions/Jenkins identity → OIDC → Vault/cloud secret manager → short-lived credential.
