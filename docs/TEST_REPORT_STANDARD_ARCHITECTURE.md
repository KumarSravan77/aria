# Standard Architecture Update Test Report

## Targeted validation

Command:

```bash
python3 -m pytest tests/test_standard_enterprise_architecture.py tests/test_aml_mlops_project.py -q
```

Result: `15 passed`

Validated:

- service-mesh and GitOps capability specs are registered
- AML golden path requires Istio/service-mesh and GitOps standards
- AML service profiles declare GitHub Actions, ArgoCD, Istio, and observability
- AML service evaluates successfully with new required capabilities
- reference Istio and ArgoCD manifests exist

## Broad suite note

A full `tests/` run in this sandbox stopped during collection because `sqlalchemy` is not installed in the runtime environment. This is an environment dependency issue, not a failure in the new standard architecture tests.
