# ARIA — LangGraph and Kubernetes Troubleshooter Integration

ARIA now includes a LangGraph-compatible investigation workflow and a deep read-only Kubernetes troubleshooter.

## LangGraph-Compatible Workflow

Location:

```text
server/investigation/langgraph/
```

Endpoints:

```text
POST /investigation-graph/invoke
POST /investigation-graph/replay
```

Capabilities:
- explicit state schema
- conditional routing
- storm degradation modes
- checkpointed node execution
- replay boundary
- safety invariant preserved

## Kubernetes Troubleshooter

Location:

```text
server/investigation/kubernetes_troubleshooter/
```

Endpoint:

```text
POST /kubernetes-troubleshooter/analyze
```

Failure modes:
- CrashLoopBackOff
- OOMKilled
- Pending
- Evicted
- NodeNotReady
- ImagePullBackOff
- ProbeFailure

The troubleshooter is read-only and never mutates infrastructure.

## Safety

The mutation boundary remains:

```text
ReBAC → policy → approval → deterministic executor → validation → audit
```
