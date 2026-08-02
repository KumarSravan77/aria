# Trivy

Use Trivy in CI before GitOps deployment.

```bash
trivy fs .
trivy image aria:local
```

Policy: do not promote vulnerable images without an approved exception.
