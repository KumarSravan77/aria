# ARIA — Istio and Thanos Investigation Agents

ARIA now treats Istio and Thanos as first-class investigation evidence sources.

## IstioAgent

Endpoint:

```text
POST /platform-agents/istio
```

Checks:
- Istiod proxy sync status
- Envoy proxy config dump boundary
- traffic policy boundary
- mTLS/canary/outlier-detection hypotheses

## ThanosAgent

Endpoint:

```text
POST /platform-agents/thanos
```

Checks:
- historical p95 latency
- historical 5xx rate
- multi-cluster/long-term metrics boundary

## LangGraph Routing

The investigation graph routes to:
- `istio` when signals include Istio, mTLS, VirtualService, DestinationRule, sidecar, Envoy, or canary
- `thanos` when signals include historical, trend, Thanos, or SLO trend

Both agents are read-only. They cannot mutate infrastructure.
