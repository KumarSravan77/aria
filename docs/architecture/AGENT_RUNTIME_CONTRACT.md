# ARIA — Agent Runtime Contract

Prompt guardrails are not enough. ARIA now includes an agent runtime contract.

## Seven Contracts

1. Identity Contract
2. Permission Contract
3. Tool Contract
4. Memory Contract
5. Observability Contract
6. Evaluation Contract
7. Reversibility Contract

## Runtime Invariant

```text
No write action without:
identity
+ permission
+ approval
+ before state
+ rollback plan
+ audit trail
+ validation
```

## API

```text
GET  /ai-runtime/contract
POST /ai-runtime/validate-action
POST /ai-runtime/sessions
POST /ai-runtime/events
GET  /ai-runtime/sessions/{id}/summary
GET  /ai-runtime/sessions/{id}/events
GET  /ai-runtime/sessions/{id}/flow
POST /ai-runtime/cache/analyze
POST /ai-runtime/replay/compare
```

## Why

A successful API call can still be semantically wrong. Runtime contracts make AI actions accountable, observable, reversible and auditable.
