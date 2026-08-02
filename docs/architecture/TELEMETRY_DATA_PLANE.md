# ARIA Telemetry Data Plane

## Scope

ARIA remains the AI-SRE control plane. This layer supplies Kubernetes collection, buffering, storage, and pipeline evidence. AI never sits in the ingestion path and an AI outage cannot interrupt telemetry.

```text
Kubernetes workloads
  -> OTel node agents
  -> OTel gateways
     -> Prometheus scrape endpoint (metrics)
     -> Tempo (traces)
     -> Redpanda/Kafka -> Vector -> Loki + object archive (logs)
  -> Grafana / Alertmanager
  -> ARIA evidence agents
```

## Deployment profiles

| Profile | Purpose | Storage |
|---|---|---|
| local | Laptop/Kind functional validation | Monolithic backends and MinIO |
| scale | HA and failure testing | Distributed Loki, Thanos and external object storage |
| search | Full-text and security investigations | OpenSearch instead of Loki hot storage |

The OpenSearch and Loki profiles are alternatives. Running both is justified only when search requirements and cost allocation are documented.

## Reliability controls

- Agent and gateway memory limiters prevent uncontrolled memory growth.
- Gateway queues survive transient exporter failure; Kafka provides longer replay windows.
- Three gateway and broker replicas remove normal single-pod failures.
- Vector scales from Kafka consumer lag.
- Collector refusal, queue utilization, Kafka lag, and Loki discards are alertable.
- Debug logs are routed away from the hot path.
- PII-like email and authorization patterns are redacted before durable storage.

Local `emptyDir` gateway queues prove queue behavior but do not survive node loss. Production overlays must use durable volumes or rely on a short gateway queue plus Kafka acknowledgements.

## Tenant model

Every exporting namespace carries `telemetry.aria.io/tenant`. OTel adds Kubernetes metadata, Vector restricts Loki labels to tenant, namespace, and service, and high-cardinality request/user identifiers remain structured fields rather than labels.

## Capacity planning

`GET /telemetry/capacity` exposes transparent planning math. A 100 TB/day plan is an estimate, not a benchmark claim. Before production sizing, replay representative payload sizes, compression, cardinality, query mixes, broker loss, object-store latency, and regional failure.

## Safe remediation

`POST /telemetry/remediation/propose` is always dry-run. Scaling, tenant quarantine, and retention changes must become reviewed GitOps changes and pass ARIA authorization, policy, approval, audit, and validation controls.
