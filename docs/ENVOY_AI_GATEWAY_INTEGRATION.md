# ARIA + Envoy AI Gateway

## Architectural decision

Envoy AI Gateway is ARIA's **AI traffic plane**. LangGraph/agents remain the reasoning and orchestration plane, RAG remains the knowledge plane, MCP/tool adapters remain the action plane, and ARIA's existing ReBAC/policy/approval/executor chain remains the mutation safety boundary.

```text
Incident / ChatOps / API
          |
          v
   ARIA orchestration
    |      |       |
   RAG   Agents   MCP/tools
          |
          | LLM inference only
          v
  Envoy AI Gateway (Tier 1)
   |        |         |
 OpenAI   Bedrock   Azure/Anthropic
                       |
                 self-hosted Tier 2
                       |
                  vLLM / GPU pool
```

## What changed in the application

1. `server/llm/client.py` defines the tiny client contract ARIA reasoning depends on.
2. `EnvoyAIGatewayClient` sends OpenAI-compatible chat-completion requests to the gateway.
3. `client_factory.py` selects `envoy-ai-gateway` or direct `ollama` for local/offline development.
4. `IncidentReasoner` no longer depends on the concrete Ollama type.
5. ARIA adds `x-tenant-id`, `x-aria-agent-id`, and `x-aria-request-id` headers to gateway calls for policy, quota, and trace correlation.
6. Token-budget accounting uses the logical gateway model when gateway mode is selected.

## Safety boundary preserved

No gateway response is executable. The model may recommend a remediation, but ARIA still requires the existing chain:

```text
LLM recommendation
    -> grounding / guardrails
    -> ReBAC authorization
    -> policy validation
    -> approval where required
    -> action executor
    -> recovery validation
```

This is deliberately unchanged.

## Model abstraction

ARIA should use logical names rather than provider model IDs:

- `aria-reasoning` — incident RCA and planning
- `aria-fast` — classification/summarization
- `aria-code` — code/config analysis
- `aria-private` — self-hosted inference for restricted data

The gateway owns the physical provider mapping and future fallback rules.

## Rollout plan

### Stage 1 — current implementation

Route the existing IncidentReasoner through Envoy AI Gateway. Preserve direct Ollama as an explicit developer fallback.

### Stage 2 — multi-provider resilience

Add Bedrock/Azure/Anthropic backends, upstream workload identity, weighted routing/fallback, health-aware policies, and token-based tenant quotas.

### Stage 3 — observability

Export gateway OpenTelemetry/OpenInference telemetry into ARIA's OTel collector. Correlate gateway request IDs with Langfuse, Dynatrace, Prometheus, and Tempo. Track TTFT, inter-token latency, input/output tokens, fallback rate, provider error rate, model availability, and cost.

### Stage 4 — MCP gateway

Put MCP traffic behind Envoy AI Gateway MCPRoute. Keep read-only investigation tools separate from mutation-capable remediation tools, and apply per-agent authorization. ARIA approval remains mandatory for protected production mutations.

### Stage 5 — self-hosted inference

Introduce the Tier-2 pattern and Gateway API Inference Extension in front of vLLM/KServe pools. `aria-private` can then route to local/self-hosted inference without changing agent code.

## SLOs to add

- AI gateway availability >= 99.99%
- successful inference requests >= 99.9%
- TTFT p95 target by model class
- provider fallback rate and fallback success
- 429/token-quota rejection rate
- MCP tool success rate
- end-to-end successful task rate

## Production rules

- Never commit provider keys.
- Prefer workload identity for AWS/Azure/GCP.
- Keep provider credentials at the gateway boundary.
- Require NetworkPolicy so ARIA cannot bypass the gateway to public model APIs.
- Pin supported Envoy AI Gateway and Envoy Gateway releases.
- Treat the logical model catalog as a platform contract.
