# ARIA Validation Status

## Current Validation State

- 208/208 tests passing
- 30/30 dry-run checks passing

## Validation Summary

| Group | Result | Key Evidence |
|---|---|---|
| Core platform | 4/4 | Health service=aria, auth 401, ReBAC 403, P1 intake |
| LangGraph graph | 5/5 | P1 broad route, SURVIVAL mode, Istio + Thanos routing, replay route match |
| K8s troubleshooter | 2/2 | CrashLoopBackOff + OOMKilled analysis |
| Istio agent | 1/1 | Graceful degrade, canary/outlier hypotheses |
| Thanos agent | 1/1 | Graceful degrade when THANOS_URL not set |
| Domain registry | 3/3 | All 6 enterprise domains loaded |
| Existing platform | 3/3 | Blast radius, SLO, healing validations |
| Webhooks | 3/3 | Falco HMAC, replay protection, Kyverno intake |

## Supported Enterprise Domains

- Capital Markets
- Retail Banking
- Wealth Management
- AML/Fraud
- Insurance
- Retail/E-Commerce

## Platform Capabilities

- LangGraph investigation orchestration
- AI-native SRE workflows
- Kubernetes troubleshooting
- Istio service mesh diagnostics
- Thanos historical metrics analysis
- Operational memory
- AI observability
- DevSecOps remediation
- GitOps PR generation
- HMAC-secured intake
- ReBAC authorization
- Approval-gated remediation
- Chaos engineering
- HA/DR planning
- Runbook intelligence
- Enterprise service skills

## Architectural Invariant

```text
AI recommends
→ ReBAC authorizes
→ Policy validates
→ Approval gates
→ Deterministic executor mutates
→ Validation confirms
→ Operational memory learns
```

## Status

ARIA is currently operating as a production-grade AI-native SRE / AIOps / DevSecOps control plane with governed autonomous investigation and recommendation capabilities.

## Kubernetes Issues Dataset

Added Kubernetes production-issues evaluation layer:

- normalized issue dataset
- failure mode classifier
- safety filter
- LangGraph replay runner
- `/evals/k8s-issues/normalized`
- `/evals/k8s-issues/replay`

This improves ARIA's Kubernetes incident benchmark, replay, and MTTR-improvement training capability.
