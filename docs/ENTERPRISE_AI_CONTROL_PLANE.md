# ARIA enterprise AI control plane

The control-plane target is a defensible AI platform, not merely an LLM endpoint.

```text
workload identity
  -> authorization and policy decision
  -> prompt/PII/groundedness guardrails
  -> Envoy AI Gateway model route
  -> RAG, dataset and model lineage
  -> evaluation and latency evidence
  -> tamper-evident audit chain
  -> production WORM/object-lock sink
```

## Implemented foundations

- Envoy AI Gateway logical model routing and tenant/request correlation headers.
- OpenFGA-ready ReBAC and policy/approval boundaries.
- LLM and agent guardrails.
- OpenTelemetry, Prometheus, Loki, Tempo and Langfuse adapters.
- Dataset and model artifact hashing and promotion policy.
- `AITransactionEvidence` contract joining identity, model, policy, guardrails, lineage, evaluation and latency.
- Concurrent-safe append-only SHA-256 evidence ledger with full-chain verification.
- Privacy enforcement that rejects prompts, responses, tokens, authorization values and secrets from audit records.

The local ledger is tamper-evident, not physically immutable. Production records must be exported to retention-locked storage such as an approved WORM system or object storage with compliance-mode retention.

## Remaining enterprise integrations

- SPIFFE/SPIRE workload identities and mTLS attestation.
- OAuth/OIDC token exchange and on-behalf-of delegation.
- Cedar or OPA policy compilation/distribution with versioned bundles.
- Region and data-residency enforcement at the gateway.
- Signed evidence export to immutable storage.
- Formal OSFI E-23/OCC control mapping and retention policy.
- Federated model/agent registry and self-service developer portal.

These integrations require enterprise identity, policy and storage systems. Their contracts should remain adapter-based so local ARIA continues to run without corporate infrastructure.
