# ARIA System Architecture

## Core Invariant

```
AI recommends
→ Deterministic systems validate
→ ReBAC authorizes
→ Policies enforce
→ Approval gates
→ Execution mutates infrastructure
→ Validation confirms outcomes
→ Memory learns
```

This invariant holds across every layer. No AI agent may directly mutate infrastructure.

## Layer Overview

### Alert Intake
HMAC + timestamp + nonce validated webhooks from Alertmanager, Falco, Kyverno, Gatekeeper.

### Investigation
LangGraph-compatible workflow with dynamic routing. Nodes: metrics, logs, traces, kubernetes_troubleshooter, istio, thanos, rag, security, healing, rca, chatops.

### Governed Remediation
ReBAC check → policy validation → 4-eyes approval → Celery async execution → outcome validation.

### Learning
OperationalMemory (PostgreSQL) + RLOptimizer (UCB1 bandit) + RemediationScorer (Jaccard similarity).

Operational outcomes enter memory as `candidate`. They cannot affect remediation ranking until an authorized incident commander verifies the root cause and evidence references. Verified records are scoped by service, team and environment, retain provenance and sensitivity, and can be superseded. Investigation checkpoints persist only bounded state summaries rather than raw logs or customer payloads.

```text
candidate outcome → evidence review → verified memory → ranking/evaluation
                                  ↘ audit record and provenance
```

### HA/DR
PDB, topology spread, Velero, Postgres DR, GitOps recovery, Istio failover, regional DR planning.
