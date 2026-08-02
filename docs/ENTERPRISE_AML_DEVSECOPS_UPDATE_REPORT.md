# Enterprise AML/MLOps + DevSecOps Update Report

## Added

- Enterprise transaction event bus standards.
- Transaction risk scoring standards.
- DevSecOps standards and tooling gates for every service/application.
- Deterministic demo AML transaction risk scorer.
- Enterprise Event Bus Agent.
- Transaction Risk Scoring Agent.
- DevSecOps Agent.
- Service Review integration for the three new agents.
- Transaction scoring API route: `/aria/platform/transactions/score`.
- Kafka topic definitions for `transactions.events` and `transactions.risk-scored`.
- Transaction event JSON schema.
- Risk model registry example.
- Example high-risk transaction event.
- Enterprise AML transaction risk architecture documentation.

## Intended runtime flow

```text
payments-api / orders-api / other transaction-producing apps
  -> transactions.events Kafka topic
  -> AML feature pipeline
  -> feature store
  -> fraud/AML model inference
  -> risk score + explanations + recommended action
  -> transactions.risk-scored topic
  -> case management / application decision flow
  -> ARIA service review + DevSecOps + SRE governance
```

## DevSecOps controls per service

- SAST: Semgrep / SonarQube
- SCA: Dependabot / Snyk
- Container scanning: Trivy / Grype
- Secret scanning: Gitleaks / TruffleHog
- IaC scanning: Checkov / tfsec
- SBOM: Syft
- Image signing: Cosign
- Policy-as-code: OPA / Conftest
- Admission policy: Kyverno / Gatekeeper
- Runtime security: Falco

## Validation

Targeted enterprise integration tests passed:

```text
8 passed
```

`compileall` passed for the updated source files.

Full repository test collection in this sandbox requires optional runtime dependencies that are not installed here: `sqlalchemy`, `celery`, and `kubernetes`. Those were pre-existing integration dependencies, not failures introduced by this update.
