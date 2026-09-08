# AI Agent Observability and Feedback Loop

## Current coverage

ARIA correlates infrastructure and AI execution using W3C/OpenTelemetry traces, runtime session events, Prometheus metrics, Loki logs, Tempo traces, Langfuse-compatible observations, Opik OTLP export, evaluation scorecards, model lineage, and tamper-evident AI transaction evidence.

Runtime events carry `trace_id`, `span_id`, `parent_span_id`, `session_id`, `workflow_id`, `agent_id`, tool, model and prompt versions, token counts, latency, status, and evaluation scores. Raw prompts and retrieved documents are excluded from durable feedback records by policy.

## Controlled deep-feedback loop

```text
agent/tool/model trace
  -> groundedness, safety, correctness and latency evaluation
  -> trace-linked user or reviewer feedback
  -> privacy and sensitive-field rejection
  -> knowledge-gap and failure-category aggregation
  -> human approval for evaluation-dataset candidacy
  -> offline regression and challenger evaluation
  -> policy-based canary promotion or rejection
  -> production monitoring and rollback
```

Feedback is evidence, not training truth. ARIA never trains directly on unreviewed user feedback and never changes a production prompt, retriever, model, permission, or guardrail without evaluation and the configured approval gate.

## Coverage boundary

The repository provides the contracts, recorder, API, exporters, evaluation, and governance path. Complete tracing still requires every deployed agent and tool adapter to create child spans, propagate context across queues and HTTP calls, and configure a durable production backend. Sampling, retention, dashboards, alerts, and SLO thresholds remain deployment responsibilities.
