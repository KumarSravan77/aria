# Telemetry Validation Runbook

## Baseline

1. Deploy the local overlay and supported backend charts.
2. Run the k6 OTLP workload at a stable rate.
3. Record accepted/refused records, queue use, broker lag, end-to-end delay, CPU, memory, and storage growth.

## Burst

Increase `RATE` fivefold for ten minutes. Pass when refusal remains zero, queues drain within the agreed recovery window, and no collector exceeds its memory limit.

## Loki outage and replay

Scale Loki writes to zero for twenty minutes. Confirm Kafka retains events, consumer lag rises, agents report the bottleneck, and sequence IDs are queryable after recovery. Compare generated, archived, and stored sequence counts.

## Noisy tenant

Send 65 percent of traffic under one tenant with debug severity. Confirm hot-storage throttling is tenant-scoped, debug traffic reaches archive, and other tenants continue within their SLO.

## Cardinality explosion

Generate unique request IDs as fields, then intentionally as labels in a sandbox. Confirm the cardinality alert fires and ARIA recommends correcting the label schema rather than scaling blindly.

## Component failure

Delete one gateway and one broker independently. Confirm availability, partition leadership recovery, queue behavior, and absence of data loss.

## Evidence record

For every run save configuration revision, start/end time, generated event count/bytes, accepted/refused count, stored count, maximum lag, recovery time, resource use, and unresolved errors. Never describe capacity as validated without this record.
