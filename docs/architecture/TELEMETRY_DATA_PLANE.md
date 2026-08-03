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
| production-small | Single production cluster with three-way ingestion and buffering | External object storage and selected hot backend |
| production-regional | Zone-spread regional ingestion with larger autoscaling envelopes | External object storage and regional hot backend |
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

Local `emptyDir` gateway queues prove queue behavior but do not survive node loss. The production profiles intentionally use the gateway queue only as a short shock absorber; acknowledged Kafka/Redpanda records are the durable replay boundary. This avoids attaching a single writable volume to a horizontally scaled Deployment.

## Tenant model

Every exporting namespace carries `telemetry.aria.io/tenant`. OTel adds Kubernetes metadata, Vector restricts Loki labels to tenant, namespace, and service, and high-cardinality request/user identifiers remain structured fields rather than labels.

## Capacity planning

`GET /telemetry/capacity` exposes transparent planning math for bytes and events per second, design peak, partitions, collector/gateway replicas, Kafka storage, and hot/archive storage. A 100 TB/day plan is an estimate, not a benchmark claim. Before production sizing, replay representative payload sizes, compression, cardinality, query mixes, broker loss, object-store latency, and regional failure.

The Terraform root under `telemetry/terraform` provisions a private, KMS-encrypted archive bucket with versioning and lifecycle tiers. It assumes the Kubernetes cluster already exists and deliberately creates no static cloud credentials.

## Log delivery invariant

The gateway writes logs to Kafka/Redpanda only. Vector is the sole consumer responsible for Loki hot storage and object archive routing. This prevents the direct-gateway and buffered-consumer paths from creating duplicate log records.

## Safe remediation

`POST /telemetry/remediation/propose` is always dry-run. Scaling, tenant quarantine, and retention changes must become reviewed GitOps changes and pass ARIA authorization, policy, approval, audit, and validation controls.
