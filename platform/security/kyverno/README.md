# Kyverno Policy Pack

Kyverno is the default Kubernetes policy-as-code engine for ARIA.

Policies included:

- require ownership labels
- require resource requests/limits
- disallow `latest` image tag
- require non-root containers
- require liveness/readiness probes
- restrict privileged containers
- require read-only root filesystem

Apply:

```bash
make kyverno-install
make kyverno-policies-apply
```
