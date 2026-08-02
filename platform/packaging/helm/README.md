# Helm Packaging

Use Helm to package ARIA and common platform dependencies. Helm is best for reusable application installation.

Recommended use:

```bash
helm upgrade --install aria ./platform/packaging/helm/aria -n sre --create-namespace
```
