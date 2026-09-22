# Read-only Kafka diagnostics

ARIA's Kafka agent can now query live cluster metadata, a named topic's
partition/replica/ISR state, and a named consumer group's committed versus
latest offsets. It does not consume messages, join a group, commit offsets,
create topics, or change broker state. The API requires authentication, an SRE
role, and ReBAC access to the incident service.
It also requires an exact service/topic/consumer-group mapping in
`server/authz/kafka_resources.yaml`; unknown mappings fail closed before any
broker query. The committed mapping is a local lab seed, not a production
service catalog. Govern and review these mappings for each deployment.

## Configure

Set `KAFKA_BOOTSTRAP_SERVERS` for the ARIA API process. For secured clusters,
also set `KAFKA_SECURITY_PROTOCOL`, `KAFKA_SASL_MECHANISM`,
`KAFKA_SASL_USERNAME`, `KAFKA_SASL_PASSWORD`, and/or
`KAFKA_SSL_CA_LOCATION` as appropriate. Keep credentials in the runtime secret
store, never in source control. Grant metadata, group-offset read, and topic
offset read permissions scoped to the intended resources. The Python runtime
installs `confluent-kafka` from `server/requirements.txt`.

For the local Redpanda telemetry overlay, use the address resolvable **from
ARIA's runtime**. The cluster-internal service name in `telemetry/` will not
resolve from a host-side Python process without networking or port-forwarding.

Run `make kafka-diagnostics-test` for deterministic adapter tests. With an
authorized API token and a configured broker, run `make kafka-agent-demo` after
editing `examples/kafka-diagnostic-request.json` to name a real topic, group,
and authorized service. A live-broker validation must record the actual topic,
group, broker setup, and timestamp separately; the synthetic Fire Drill demo
does not perform it.

## Evidence semantics

- `cluster.available` means broker metadata was returned, not that the entire
  cluster is healthy.
- `topic_health` reports offline and under-replicated partitions from a single
  metadata snapshot, not throughput or ISR history.
- `consumer_lag.total_lag` is present only when every named partition has a
  valid committed offset and end offset. Missing commits and offset regressions
  are unknown, never treated as zero lag.
- `live_evidence_complete` is true only when cluster, topic, and group-offset
  queries all succeed. Missing access/dependency/broker data remains explicit.
- Rebalance storms and hot keys still require time-series metrics; a single
  Kafka metadata/offset snapshot cannot prove either cause.

All queries are timeout-bounded and limited to 128 partitions per topic. Error
responses omit raw Kafka exception text to avoid leaking addresses or secrets.
Topic metadata is fetched without a topic-name request to avoid broker-side
topic auto-creation on clusters configured to allow it.
