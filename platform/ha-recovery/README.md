# HA/DR Recovery Layer

This layer adds high-availability and disaster-recovery patterns to ARIA.

## Capabilities

- PodDisruptionBudget examples
- topology spread and anti-affinity examples
- Velero backup/restore examples
- Postgres disaster recovery runbook
- GitOps recovery with Argo CD
- traffic failover examples
- regional DR guidance
- RTO/RPO tracking
- AI-assisted recovery planning

ARIA should not execute destructive recovery automatically. Recovery actions must pass ReBAC, policy validation, approval, and audit logging.
