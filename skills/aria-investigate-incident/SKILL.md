---
name: aria-investigate-incident
description: Investigate ARIA banking-platform incidents across CI/CD, Kubernetes, GitOps, telemetry, changes, runbooks, and verified memory. Use for Jenkins failures, broken deployments, Kubernetes failures, SLO alerts, production debugging, RCA, or governed remediation recommendations.
---

# Investigate an ARIA incident

1. Read `AGENTS.md`, the system architecture, and threat model.
2. Establish incident, service, owner, environment, severity, UTC interval and last known good state.
3. Build a timeline before diagnosis and collect minimum authorized evidence.
4. Follow [references/investigation-workflow.md](references/investigation-workflow.md).
5. Separate observations, hypotheses, tests and conclusions; find the first causal failure.
6. Cite build IDs, commits, image digests, object identities, query windows and runbook versions.
7. Use only verified operational memory to rank remedies; revalidate it against current evidence.
8. Return causal chain, blast radius, confidence, mitigation, durable fix, validation and unknowns.
9. Keep mutations behind ReBAC, policy, approval, deterministic execution, audit and validation.

Never request unrestricted shell access, expose sensitive data, bypass controls, or claim unavailable evidence was checked.
