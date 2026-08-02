# ARIA Spec-Driven Platform Layer

ARIA now defines platform behavior through versioned specs instead of hidden agent logic.

## What was added

- Capability specs for Kubernetes, observability, CI/CD, and reliability standards
- Golden path specs for Java Spring Boot Tier-1 and Python AI services
- Service profile specs for onboarded applications
- Production governance policy specs
- AI decision specs for rollback, scale-out, and PR creation
- Remediation specs for Kubernetes failure modes
- Workflow specs for service review and onboarding
- A deterministic `SpecDrivenEvaluator` and CLI script
- GitHub Actions spec validation workflow

## Development model

```text
Write spec → Add fixture/profile → Add harness/test → Implement agent/check → Validate report
```

## Why this matters

This makes ARIA safer and more enterprise-ready because AI behavior becomes:

- auditable
- versioned
- testable
- policy-driven
- deterministic where needed
- approval-gated for production mutations

## Example

```bash
python scripts/spec_evaluate.py payments-api
```

The evaluator loads the service profile, resolves the golden path, verifies required platform capabilities, loads governance policies, and returns a machine-readable result.
