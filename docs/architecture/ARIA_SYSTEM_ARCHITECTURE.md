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

### HA/DR
PDB, topology spread, Velero, Postgres DR, GitOps recovery, Istio failover, regional DR planning.
