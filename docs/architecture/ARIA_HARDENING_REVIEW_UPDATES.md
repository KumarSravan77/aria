# ARIA — Hardening Review Updates

This update adds code-level hardening based on the deep review.

## Added

### Safety
- `server/safety/degradation.py`
- `server/safety/dry_run_policy.py`
- `server/safety/mutation_guard.py`

### LangGraph Reliability
- `state_utils.py` with state merge, evidence dedupe and route budget
- `replay_context.py` for deterministic replay control
- route budgeting wired into graph execution

### Evaluation
- route correctness scoring
- RCA scoring
- remediation safety scoring
- combined evaluation scorecard
- `/evals/scorecard`

### AI Observability
- trace sampling policy

### Operational Memory
- memory compaction boundary

## Why

ARIA is now large enough that the main risk is not missing features, but:
- safety bypass
- routing explosion
- replay inconsistency
- duplicate evidence
- unsafe recommendations
- unbounded memory
- trace explosion

This update adds foundation controls for those risks.
