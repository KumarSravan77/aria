# Regional Disaster Recovery Guide

## Patterns

- Active-passive: simpler, lower cost, higher RTO.
- Active-active: higher cost, lower RTO, more operational complexity.

## Recovery sequence

1. Confirm regional impact.
2. Freeze risky automation.
3. Restore state using Velero/database backups.
4. Sync apps using GitOps.
5. Shift traffic through DNS/Gateway/Istio.
6. Validate SLOs and RTO/RPO.
7. Generate RCA and resilience report.
