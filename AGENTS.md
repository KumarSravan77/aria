# AGENTS.md — Repository Instructions for AI Coding Agents

This repo is designed to be maintained by AI coding tools such as Claude Code, Cursor, and other agentic development tools.

## Mission

Build and maintain an open-source AI-SRE incident investigation platform that combines Kubernetes observability, RAG-based runbooks, and policy-controlled self-healing.

## Repository Skills and Runbooks

- Read the relevant portable skill under `skills/` before investigation, runbook, or MCP connector work.
- Treat `docs/runbooks/` as the canonical Markdown RAG corpus.
- Only verified operational outcomes may influence learning or remediation ranking.
- Keep README, architecture, runbooks, examples, correlation rules and tests aligned.

## Non-Negotiable Guardrails

- Do not bypass `server/healing/policy_validator.py`.
- Do not add direct destructive Kubernetes actions.
- Do not allow the LLM to run arbitrary commands.
- Do not store secrets in the repo.
- Do not hardcode production credentials, tokens, kubeconfigs, or API keys.
- Do not make production-only assumptions; this repo must run locally first.

## Preferred Implementation Style

- Python 3.11+
- FastAPI routes should be small and delegate to services.
- Correlation logic should be deterministic and testable.
- RAG retrieval should return sources.
- Self-healing should be explicit action functions.
- Policy should be YAML-driven where possible.
- Tests should be added for every new action or incident type.

## Definition of Done for New Incident Scenario

A new incident scenario is complete only when it includes:

- Markdown runbook
- Example incident payload
- Correlation rule
- Test case
- RAG source coverage
- Optional remediation policy
- Optional remediation action
- README/docs update

## Safe Remediation Categories

Allowed low-risk examples:

- scale deployment within approved min/max
- restart deployment
- restart non-critical pod
- trigger read-only diagnostics

Approval-required examples:

- production rollback
- node drain
- service mesh traffic shift
- high replica increase

Forbidden autonomous examples:

- delete namespace
- delete PVC/PV
- delete database
- rotate secrets
- terraform destroy/apply
- disable security controls

## Collaboration / AI War Room Agent Guidance

When working on the collaboration layer:

- Use `server/collaboration/` as the boundary for Slack, Mattermost, and local simulation.
- Preserve local-first behavior so the repo runs on any laptop.
- Treat Slack/Mattermost channel creation as an adapter concern, not core business logic.
- Add tests for timeline and message formatting when changing AI teammate behavior.

## Enterprise Tool Integration Guidance

When modifying integrations:

- Keep every external system behind a small adapter class.
- All adapters must fail closed or degrade gracefully.
- Never let an unavailable optional tool break incident creation.
- Add a Make target and a doc page for every new integration.
- Do not add heavyweight ML dependencies to the Kubernetes API image unless explicitly required.
- Prefer slim images and lazy initialization for local Kind compatibility.

## Enterprise adapters

When editing enterprise adapters, keep the graceful-degradation contract:

```json
{"available": false, "error": "..."}
```

For mutation paths, keep the approval/queue model:

```text
request -> auth -> ReBAC -> approval -> Celery worker -> deterministic executor -> audit
```

## Chaos Engineering Agent Context

The chaos subsystem validates resilience using LitmusChaos. Treat it as a controlled test harness, not a production mutation tool.

Important files:
- `server/chaos/experiment_catalog.py`
- `server/chaos/litmus_client.py`
- `server/chaos/validation_engine.py`
- `server/chaos/chaos_reporter.py`
- `k8s/chaos/*.yaml`
- `docs/chaos/LITMUS_CHAOS_RESILIENCE.md`

Required safety invariants:
- Auth required
- ReBAC required
- Dry-run default
- No AI direct execution
- Live Litmus runs only in sandbox unless policy/approval is added

## Agentic Operations Layer

The repo now has deterministic agentic scaffolding under `server/agents/`:

- metrics
- logs
- traces
- Kubernetes
- RAG
- healing proposal
- RCA
- ChatOps

Keep the hard boundary: agents are evidence producers and recommendation engines. They are not executors.


## Full-maturity hardening notes

- Chaos is disabled by default. Set `CHAOS_ENABLED=true` only in a sandbox cluster.
- Multi-agent investigations run agents in parallel but preserve stable response ordering.
- Operational memory is now persisted through the database when a DB session is available.
- Chaos validation APIs use an explicit request-to-engine contract instead of passing schema dumps directly.

## Platform tooling agent guidance

For Kubernetes-native tooling changes:

1. Treat `platform/` as declarative examples and operational guidance.
2. Treat `server/platform/` as API-level planning/registry logic.
3. Do not wire a new tool into live execution unless it has dry-run behavior, ReBAC checks, approval, and audit logging.
4. Canary deployment defaults should use Argo Rollouts, Istio, and Prometheus analysis.
5. Security defaults should include Kyverno policies for labels, probes, resources, non-root, no latest tag, and no privileged containers.


## HA/DR Recovery Layer

ARIA now includes high-availability and disaster-recovery planning.

Capabilities:
- `/recovery/plan` creates advisory recovery plans for pod, node, DB, cluster, and regional failures.
- `/recovery/validate` validates recovery controls after an incident or chaos experiment.
- `/recovery/rto-rpo` compares actual recovery metrics against RTO/RPO targets.
- `platform/ha-recovery/` contains PDB, topology spread, Velero, Postgres DR, GitOps recovery, Istio traffic failover, and regional DR examples.

Safety boundary: HA/DR recovery planning is advisory. Destructive recovery actions must pass ReBAC, policy validation, approval, and audit logging.


## Operational Intelligence Last-Mile Layer

ARIA now includes the last-mile operational integrations:

- Observability correlation across Prometheus, Loki, Tempo and Hubble.
- SLO burn-rate alert payload generation.
- Chaos schedule planning and resilience trend recall.
- Kyverno/Gatekeeper policy violation incident ingestion.
- ChatOps approval cards and threaded AI evidence updates.
- LLM hallucination guardrails that require retrieved sources or telemetry evidence before output is treated as actionable.

Safety rule: AI can recommend only. ReBAC, policy validation, 4-eyes approval, audit logging, and deterministic executors own all mutations.

## AI Agent Safety Context

All coding agents must preserve:

- ReBAC before data access
- policy validation before remediation
- approval before risky execution
- audit logging after execution
- groundedness checks for LLM/RAG output

See:
- `docs/architecture/ARIA_SYSTEM_ARCHITECTURE.md`
- `docs/security/ARIA_THREAT_MODEL.md`
