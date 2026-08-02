# ARIA — Kafka Streaming Intelligence

ARIA now treats Kafka as a first-class operational layer for enterprise applications.

## Why Kafka Matters

Kafka is central for:

- Capital Markets market data and trade lifecycle events
- Retail Banking payment events
- AML/Fraud transaction monitoring
- Wealth analytics
- Insurance workflow events
- Retail/e-commerce checkout/order/inventory streams

## Added Components

```text
server/platform/streaming/kafka/
├── client.py
└── analyzers.py

server/agents/kafka_agent.py
```

## Endpoint

```text
POST /platform-agents/kafka
```

## LangGraph Routing

The investigation graph now routes to the Kafka node when incident signals include:

- kafka
- consumer lag
- lag
- rebalance
- topic
- partition
- ISR
- broker
- streaming

## Kafka Failure Modes

| Failure | ARIA Evidence |
|---|---|
| Consumer lag | lag growth, processing delay, downstream dependency latency |
| Rebalance storm | group instability, deployment timing, consumer restarts |
| Partition skew | hot partition, uneven lag, key distribution |
| Broker saturation | ISR shrink, disk/network pressure |
| Poison message | repeated offset failure, DLQ growth |

## Safety

KafkaAgent is read-only.

It cannot:
- delete topics
- change ACLs
- reset offsets
- alter partitions
- mutate broker config

Any remediation remains behind:

```text
ReBAC → policy → approval → deterministic executor → validation → audit
```
