# GitHub Actions for ARIA Multi-Application Platform

ARIA supports multiple onboarded applications through `config/applications.yaml`.
Each service declares its path, language, Dockerfile, Helm chart, tier, owner team,
and service profile. The GitHub Actions matrix converts this catalog into reusable
CI/CD jobs.

## Workflows

| Workflow | Purpose |
|---|---|
| `multi-app-platform-ci.yml` | Runs the shared platform CI flow for every onboarded app. |
| `reusable-app-ci.yml` | Language-aware build/test workflow for Java, Node.js, and Python services. |
| `reusable-security-scan.yml` | Gitleaks, Trivy filesystem scan, and SBOM generation. |
| `reusable-docker-build.yml` | Builds service container images. Push is disabled by default for safe local adoption. |
| `reusable-aria-service-review.yml` | Runs ARIA harness tests and emits a service review artifact. |
| `ai-devops-on-failure.yml` | Triggers ARIA failure analysis when platform CI fails. |

## CI vs CD

GitHub Actions is the CI layer: build, test, scan, package, and image creation.
ArgoCD remains the CD/GitOps layer: it deploys Kubernetes state from Git to the cluster.

```text
Developer Push
  -> GitHub Actions CI
  -> Build/Test/Scan/Image
  -> Update GitOps repo or Helm values
  -> ArgoCD Sync
  -> Kubernetes Deployment
  -> ARIA observes reliability, SLOs, and incidents
```

## Multi-Application Model

Add a new service to `config/applications.yaml`:

```yaml
applications:
  - service_id: orders-api
    app_path: apps/orders-api
    language: java
    dockerfile: apps/orders-api/Dockerfile
    helm_chart: k8s/charts/orders-api
    service_profile: examples/self_service/service_review_request.json
    tier: tier1
    owner_team: payments
```

The same CI, security, Docker, and ARIA service-review workflows will run for the new service.

## AI DevOps Failure Agent

When a GitHub Actions workflow fails, `ai-devops-on-failure.yml` creates a normalized
failure event. ARIA then classifies the failure, sanitizes untrusted logs, retrieves
ReBAC-authorized runbooks, and prepares a dry-run remediation plan.

Production remediation should stay approval-gated.
