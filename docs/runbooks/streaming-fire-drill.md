---
id: RB-STREAM-001
title: Controlled streaming fire drill investigation
service: payment-events
domain: platform
team: payments
environment: staging
severity: SEV2
doc_type: runbook
version: 0.1.0
last_reviewed: 2026-09-22
review_cycle_days: 90
tags: [kafka, streaming, chaos, fire-drill]
sources: [fire-drill, openmodelops, prometheus, kafka]
required_permissions: [runbook:read, telemetry:read]
---

# Controlled streaming fire drill investigation

## Purpose and scope

Investigate a controlled development or staging experiment whose plan and
observations originated in Fire Drill and were evaluated by OpenModelOps.

## Customer and business impact

Confirm which synthetic event journeys missed the on-time objective. A lab
finding does not establish real customer impact or data loss.

## Preconditions and access

Use authorized read access to the experiment report, streaming metrics, Kafka
metadata, and incident timeline. ARIA's Kafka agent is read-only.

## Detection signals

| Signal | Source/query | Threshold | Meaning |
|---|---|---|---|
| Consumer lag | OpenModelOps snapshot and consumer metrics | ≥10,000 records | Processing backlog |
| Partition skew | Per-partition lag | One partition >2× mean and ≥1,000 records | Possible hot key |
| Rebalances | Consumer-group metrics | ≥5 in five minutes | Group instability |
| On-time completion | Closed event cohort | Below configured target | Error-budget impact |

## Evidence collection

| Step | Risk | Evidence | Expected result |
|---|---|---|---|
| 1 | read-only | Compare experiment and event IDs, plan digest and observation digest | IDs and digests agree across all systems |
| 2 | read-only | Record approver, namespace, duration, blast radius and stop conditions | Experiment remains within approved bounds |
| 3 | read-only | Collect before, during and after producer, consumer, partition and latency windows | Symptoms have a clear time boundary |
| 4 | read-only | Query ARIA Kafka agent for cluster, topic and consumer-group evidence | State whether live broker diagnostics were available |

## Decision tree

```text
Experiment bounds exceeded? -> stop through Fire Drill and page commander.
Cluster unavailable? -> collect broker/quorum evidence and stop experiment.
Lag concentrated on one partition? -> inspect key distribution and assignment.
Rebalances rising? -> inspect membership churn and deploy timeline.
No independent broker metrics? -> mark RCA unconfirmed and request evidence.
```

## Mitigation

Stop the experiment through Fire Drill if a stop condition fires. Any production
change to broker, topic, group, or deployment is `approval-required`; no AI
agent may execute it from this runbook.

## Recovery validation

- Confirm the experiment stopped or its planned duration ended.
- Confirm backlog drains and on-time completion returns to baseline.
- Confirm no duplicate side effects, DLQ growth, or data-integrity concern.
- Record recovery time and a stable observation window.

## Escalation

Page the streaming owner and incident commander for offline partitions,
unbounded lag, missed stop conditions, or uncertain data integrity. Include the
full evidence chain and current rollback state.

## Rollback

Use the approved Fire Drill stop/rollback procedure. Mark all live rollback
actions `approval-required` and record the actor and result.

## Evidence and audit record

Retain experiment and event IDs, immutable plan digest, observation digest,
timestamps, source metrics, findings, approvals, actions, and outcome. Separate
observed symptoms from confirmed root cause.

## Related resources

- OpenModelOps cross-repository demo: `examples/streaming-fire-drill/README.md`
- ARIA Kafka agent: `server/agents/kafka_agent.py`
- Fire Drill experiment guide: `fire-drill-chaos-engineering/README.md`
