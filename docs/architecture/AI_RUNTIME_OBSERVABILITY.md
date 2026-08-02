# ARIA — AI Runtime Observability

ARIA now includes Copilot-debug-log style AI runtime observability.

## Tracks

- session lifecycle
- graph nodes
- tool calls
- RAG calls
- token counts
- cache hit rate
- errors
- duration
- flow graph
- replay comparison

## Debug Log

```text
logs/ai_runtime_debug.jsonl
```

Each line is a structured runtime event.

## Purpose

This makes ARIA observable as an AI system, not only as an infrastructure system.
