# ARIA Hardening Fixes from Code Review

This update closes the safety and authorization gaps identified in the ARIA code review.

## Critical fixes

1. `/heal` no longer executes Kubernetes directly. Any non-dry-run mutation is converted into an approval/action row, queued, audited, and dispatched through the worker executor path.
2. `/investigate` now performs ReBAC service authorization before writing incident records.
3. `/approvals/{id}/execute` now checks ReBAC authorization against the approval target before dispatching execution.
4. `execute_approved_action` now locks the `IncidentAction` row with `with_for_update()` before claiming execution, preserving the exactly-once mutation invariant on production databases that support row locks.

## High/medium fixes

- `LazyRagService` dispatch order is now `answer -> ask -> query`.
- Falco Makefile sample now sends `X-Incident-Signature`, matching the API.
- Bearer token parsing is no longer indefinitely cached, so runtime secret rotation is not blocked by process-local cache.
- Empty namespaces no longer bypass namespace ReBAC checks.
- Stale RUNNING reset refuses to requeue already executed actions.
- Orphan approval records cannot bypass the four-eyes guard.

## Regression coverage

Added `tests/test_code_review_hardening_regressions.py` for:

- RAG dispatch contract order
- empty namespace ReBAC denial
- orphan approval rejection
- stale RUNNING + executed guard
- approved action execution path using the guarded executor flow
