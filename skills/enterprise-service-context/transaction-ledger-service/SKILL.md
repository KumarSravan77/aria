---
name: transaction-ledger-service-service-context
description: Enterprise service context for transaction-ledger-service
user-invocable: true
---

# transaction-ledger-service

## Domain
Retail Banking

## Purpose
Production enterprise microservice managed by ARIA.

## AI Investigation Flow

```text
Alert
→ Metrics
→ Logs
→ Traces
→ Kubernetes diagnostics
→ RCA
→ Remediation recommendation
→ Approval workflow
→ Validation
→ Operational memory
```

## Allowed AI Actions

- retrieve metrics/logs/traces
- generate RCA
- propose GitOps PR
- suggest rollback
- recommend scaling
- update runbook proposal

## Forbidden Actions

- direct production mutation
- bypass approvals
- merge PRs automatically
- disable security controls

## Safety Invariant

```text
AI recommends
→ ReBAC authorizes
→ Policy validates
→ Approval gates
→ Deterministic executor mutates
→ Validation confirms
→ Memory learns
```
