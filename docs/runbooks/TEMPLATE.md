---
id: RB-DOMAIN-000
title: Replace with incident title
service: service-registry-id
domain: platform
team: owning-team
environment: all
severity: SEV2
doc_type: runbook
version: 0.1.0
last_reviewed: 2026-08-03
review_cycle_days: 90
tags: []
sources: [prometheus, loki, tempo, kubernetes]
required_permissions: [runbook:read, telemetry:read]
---

# Replace with incident title

## Purpose and scope
Define the failure and exclusions.

## Customer and business impact
Describe affected journeys, data-integrity risk, and regulatory implications.

## Preconditions and access
List least-privilege read scopes. Do not include secrets.

## Detection signals
| Signal | Source/query | Threshold | Meaning |
|---|---|---|---|
| Example | Prometheus | Define | Define |

## Evidence collection
| Step | Risk | Evidence | Expected result |
|---|---|---|---|
| 1 | read-only | Query authorized telemetry | Record timestamp and result |

## Decision tree
```text
Start
└─ Deployment correlated?
   ├─ Yes: inspect pipeline, change, rollout and pod evidence
   └─ No: inspect dependencies, saturation and platform events
```

## Mitigation
Document reversible mitigations and mark production changes `approval-required`.

## Recovery validation
- Original symptom cleared.
- Error rate, latency and saturation meet SLO.
- No data-integrity concern remains.
- Stability window completed.

## Escalation
Define condition, team/role, and required evidence package.

## Rollback
Use approved GitOps or pipeline rollback; never give AI unrestricted commands.

## Evidence and audit record
Record query windows, links, change/build IDs, image digests, approvals and outcomes.

## Related resources
- Dashboard: TBD
- Jira change: TBD
- Previous RCA: TBD
