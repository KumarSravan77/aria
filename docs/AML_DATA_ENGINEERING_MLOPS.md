# AML/Fraud Data Engineering + MLOps Project

This module extends ARIA with a spec-driven AML/Fraud platform pattern for data pipelines and ML operations.

## Flow

Raw transactions → Kafka/stream ingestion → feature engineering → feature store → model training → MLflow registry → inference service → drift monitoring → ARIA service review.

## What ARIA Reviews

- Data quality, schema validation, lineage, SLA/freshness and idempotent replay.
- Model registry, explainability, drift detection, bias/fairness checks, retraining triggers and FINTRAC audit trail.
- Kubernetes, observability, CI/CD, reliability and secrets standards through existing ARIA capabilities.

## Services

- `fraud-detection-engine`: Java streaming inference engine using `java-springboot-tier1`.
- `aml-feature-pipeline`: Python data/MLOps service using `python-aml-mlops`.
