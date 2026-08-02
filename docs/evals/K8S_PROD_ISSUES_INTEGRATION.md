# ARIA — Kubernetes Production Issues Dataset Integration

ARIA now includes a Kubernetes production-issues evaluation layer.

## Purpose

Use Kubernetes production issue scenarios as:

- synthetic incident tests
- LangGraph replay inputs
- Kubernetes troubleshooter benchmarks
- RCA quality checks
- MTTR improvement training data
- runbook seed material after human review

## Important Safety Rule

The dataset is not treated as trusted production guidance.

Every issue is tagged with:

- `training_only`
- `source_verified`
- `needs_review`
- `safe_for_training`
- `unsafe_patterns`

Scenarios can be used for evaluation and replay. They must be reviewed before becoming production runbooks.

## Modules

```text
server/evals/k8s_issues_dataset/
├── importer.py
├── normalizer.py
├── classifier.py
├── safety_filter.py
├── replay_runner.py
└── router.py
```

## Endpoints

```text
GET  /evals/k8s-issues/normalized
POST /evals/k8s-issues/replay
```

## Covered Failure Modes

- CrashLoopBackOff
- OOMKilled
- Pending / Unschedulable
- ImagePullBackOff
- NodeNotReady
- Evicted
- Service Mesh / Istio
- DNS failure
- General Kubernetes

## Replay Flow

```text
K8s issue
→ normalize
→ classify failure mode
→ safety filter
→ convert to ARIA incident
→ invoke LangGraph workflow
→ measure route and agent coverage
```

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
