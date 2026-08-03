# CLAUDE.md — ARIA (Autonomous Resilience Intelligence Assistant)

ARIA is an enterprise-grade AI-native SRE incident intelligence and governed remediation platform.

## What it does

1. Receives alerts from Prometheus Alertmanager, GoAlert, Slack, or manual API.
2. Normalizes alerts into incidents.
3. Stores incidents, timelines, approvals, actions, RCA drafts, and audit logs in PostgreSQL.
4. Creates a dedicated Slack/Mattermost/stdout war-room channel.
5. Runs an AI teammate that posts debugging evidence and next steps.
6. Uses RAG over runbooks, RCA docs, SOPs, and known errors.
7. Validates remediation through policy before any self-healing action.
8. Requires approvals for risky or production-like actions.
9. Uses LitmusChaos to generate controlled Kubernetes incidents.

## Main safety rule

Never allow the LLM to directly execute commands. All actions must be structured, policy-validated, audited, and approved when required.

## Portable Skills and Runbooks

Read the matching `skills/aria-investigate-incident/SKILL.md`, `skills/aria-author-runbook/SKILL.md`, or `skills/aria-add-mcp-connector/SKILL.md`. Treat `docs/runbooks/` as the canonical RAG corpus and never promote unverified AI conclusions into trusted memory.

## Key folders

- `server/api`: FastAPI routes
- `server/intake`: alert parsers
- `server/incidents`: repository + state machine
- `server/collaboration`: Slack/Mattermost/stdout war-room adapters
- `server/approvals`: approval workflow
- `server/healing`: policy + Kubernetes actions
- `server/db`: SQLAlchemy models
- `server/workers`: Celery tasks
- `k8s/chaos`: LitmusChaos scenarios
- `docs/runbooks`: RAG runbooks
- `docs/architecture`: platform architecture

## Development rules

- Add tests for new incident parsing, state transitions, and healing policies.
- Every new incident scenario must have a runbook and sample payload.
- Do not bypass `PolicyValidator`.
- Prefer Kubernetes Python client over shelling out to kubectl.
- Keep adapters replaceable: stdout, Slack, Mattermost.

## ReBAC and Confluence Rules

- Use `server/authz/authorization_service.py` for resource access checks.
- Never retrieve RAG chunks without ReBAC metadata filtering.
- Every runbook/wiki page must include `service`, `team`, and `doc_type` metadata.
- Confluence ingestion logic lives under `server/connectors/confluence/`.
- Local OpenFGA-style relationships are in `server/authz/relationships.yaml`.
- Production OpenFGA model examples are under `infra/openfga/`.

## New AI-native Integration Rules

- Ollama is the local LLM provider. It can summarize and reason, but must never execute actions.
- Argo CD and Argo Rollouts are the preferred remediation path for deployment rollback, sync, canary promote, and canary abort.
- Prometheus, Loki, Tempo, Cilium/Hubble, and OpenCost adapters are evidence sources only.
- KEDA recommendations must be GitOps-reviewed or policy-approved before production rollout.
- Falco alerts become security incidents and must follow the same intake, ReBAC, timeline, and RCA flow.
- OpenFGA is the production target for ReBAC; local YAML relationships remain for laptop-first development.

## Enterprise tool safety rules

- Do not add direct mutation endpoints for Argo CD, Argo Rollouts, Kubernetes, or scaling without Auth + ReBAC + Policy/Approval + Audit.
- If a tool adapter is not implemented, return `available:false` or `implemented:false`; do not pretend execution happened.
- Falco and Alertmanager webhooks must use HMAC validation, not bearer auth.
- Cost, topology, logs, traces, and runbook retrieval must remain ReBAC-scoped.
- Ollama/LLM output is recommendation-only and must never execute infrastructure actions directly.

## Chaos Engineering Rules

This repo includes a LitmusChaos subsystem under `server/chaos/`, `k8s/chaos/`, and `docs/chaos/`.

When changing chaos code:
- Keep `dry_run=true` as the default for every chaos execution path.
- Never let an LLM directly apply ChaosEngine manifests.
- Enforce auth and ReBAC before running or validating chaos experiments.
- Return structured `available: false` responses when Kubernetes/Litmus is unavailable.
- Every new chaos experiment needs: catalog entry, manifest, Make target, docs, and validation expectations.
- Chaos validation should measure alerting, incident creation, RAG evidence, remediation/recovery, MTTR, and SLO signal.

## Full Maturity Rules

When changing the multi-agent, SLO, memory, deployment intelligence, or ChatOps layers:

- Agents may recommend but must never mutate infrastructure directly.
- Any live remediation must go through ReBAC, policy, approval, and Celery execution.
- SLO calculations should be explainable and deterministic.
- ChatOps commands must parse intent only; execution belongs to approved backend workflows.
- Operational memory must not leak cross-team incident details; apply ReBAC before recall or retrieval.
- Deployment correlation should be treated as evidence, not final RCA truth.


## Full-maturity hardening notes

- Chaos is disabled by default. Set `CHAOS_ENABLED=true` only in a sandbox cluster.
- Multi-agent investigations run agents in parallel but preserve stable response ordering.
- Operational memory is now persisted through the database when a DB session is available.
- Chaos validation APIs use an explicit request-to-engine contract instead of passing schema dumps directly.

## Kubernetes-native tooling rule

When modifying platform integrations:
- Treat Argo Rollouts, Karpenter, Kyverno, Gatekeeper, Thanos, Istio, VPA, Cluster Autoscaler, kOps, Rancher, and Cluster API as platform capability layers.
- Do not make AI agents execute direct cluster mutations.
- Canary promotion/abort, Argo sync, chaos experiments, and scaling must remain gated by ReBAC, policy, approval, and audit.
- Kyverno is the primary policy-as-code layer. Gatekeeper is supported as an additional admission policy option.

## Kubernetes-native tooling rules

When modifying the platform tooling layer:

- Keep Kyverno as the default policy-as-code engine.
- Keep OPA Gatekeeper as a supported admission-policy option, not the default.
- Use Argo Rollouts + Istio + Prometheus for canary plans.
- Use Helm for packaging and Kustomize for environment overlays.
- Use Karpenter as the preferred modern node autoscaler and Cluster Autoscaler as a supported legacy option.
- Do not make chaos, rollout promotion, Argo sync, or policy changes execute without ReBAC + policy + approval.
- Add documentation and tests whenever a new platform tool folder is added.


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

## Required Architecture Context

Before making major changes, read:

- `docs/architecture/ARIA_SYSTEM_ARCHITECTURE.md`
- `docs/security/ARIA_THREAT_MODEL.md`

Never bypass the ARIA safety invariant:

AI recommends → ReBAC authorizes → Policy validates → Approval gates → Deterministic execution → Validation confirms.
