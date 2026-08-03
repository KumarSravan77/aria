---
id: RB-PAY-001
title: Payment API CI/CD deployment failure
service: payment-processing-api
domain: payments
team: payments-platform
environment: all
severity: SEV2
doc_type: runbook
version: 1.0.0
last_reviewed: 2026-08-03
review_cycle_days: 90
tags: [banking, payments, jenkins, kubernetes, argocd, image-pull]
sources: [jenkins, jira, argocd, kubernetes, prometheus, loki, tempo, ecr]
required_permissions: [runbook:read, cicd:read, change:read, kubernetes:read, telemetry:read]
---

# Payment API CI/CD deployment failure

## Purpose and scope
Diagnose failed builds, image publication, GitOps synchronization, rollout, or verification without authorizing production mutation or transaction-data access.

## Customer and business impact
A failed deployment normally leaves the last healthy release serving. Escalate to SEV1 when payment processing is unavailable, error budget burns rapidly, or transaction integrity is uncertain.

## Preconditions and access
Use read-only Jenkins, Jira, Argo CD, ECR, Kubernetes and telemetry access. Redact credentials and customer/account data.

## Detection signals
| Signal | Source | Meaning |
|---|---|---|
| Failed stage | Jenkins | First causal failure, excluding skipped stages |
| Degraded application | Argo CD | Desired state did not become healthy |
| ImagePullBackOff | Kubernetes events | Image, registry, architecture or manifest issue |
| Increased 5xx/latency | Prometheus/Tempo | Possible customer impact |

## Evidence collection
1. **Read-only:** Capture build ID, commit, branch, failed stage and first error.
2. **Read-only:** Resolve Jira change, approvals, window and scope.
3. **Read-only:** Compare pipeline image tag/digest with ECR and GitOps.
4. **Read-only:** Inspect Argo sync/health and Kubernetes rollout/events.
5. **Read-only:** Correlate metrics, logs and traces in one UTC window.

## Decision tree
```text
First failure
├─ build/test -> changed component or executor/dependency failure
├─ publish -> missing artifact or identity/repository denial
├─ GitOps -> invalid policy/manifest or drift
└─ rollout
   ├─ ImagePullBackOff -> image/digest/permission/architecture
   ├─ CrashLoopBackOff -> logs/config/dependency startup
   ├─ readiness -> probe/dependency evidence
   └─ SLO regression -> stop promotion and propose rollback
```

## Mitigation
- **Read-only:** Preserve the healthy replica set and collect evidence.
- **Dry-run:** Generate and validate a Jenkinsfile or manifest patch.
- **Approval-required:** Abort a canary, revert GitOps, or rerun production deployment.
- **Forbidden-for-AI:** Bypass controls, disable policy, imperatively edit production, or access payment payloads.

## Recovery validation
Confirm pipeline gates, Argo health, replicas, synthetic checks, SLO stability, and no ledger/reconciliation concern.

## Escalation
Provide incident/build/change IDs, image digest, Argo revision, cluster/namespace, UTC interval and evidence links to the payments incident commander.

## Rollback
Use approved GitOps revert or pipeline rollback with ReBAC, policy, four-eyes approval, audit and validation.

## Evidence and audit record
Record causal stage, revisions, approvals, outcome and whether the runbook resolved the incident.

## Related resources
- `docs/platform/CI_CD_AND_AI_ISSUE_RESPONSE.md`
- `docs/security/ARIA_THREAT_MODEL.md`
