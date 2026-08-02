# AML/MLOps Test Report

## Scope

This report covers the AML/Fraud Data Engineering + MLOps extension added to ARIA.

## Added

- `python-aml-mlops` golden path
- `data-pipeline-standards` capability
- `model-governance` capability
- `fraud-detection-engine` service profile
- `aml-feature-pipeline` service profile
- `mlops-remediations` remediation spec
- `mlops-deployment-workflow` workflow spec
- synthetic AML transaction dataset
- model drift scenario dataset
- AML model drift scenario catalog entry
- Canadian enterprise service registry entry

## Validation

- AML/MLOps targeted tests: `10 passed`
- Full test suite: `317 passed`
- Import smoke check: `232 modules scanned`, `0 import failures`

## Remaining Production Work

This extension is spec-driven and harness-ready. Real production integrations still need live connectors for Kafka, Airflow, Spark/Databricks, MLflow, Feast, KServe, and monitoring systems.
