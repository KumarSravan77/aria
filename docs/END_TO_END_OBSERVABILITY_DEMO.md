# End-to-End Observability Demo

This scenario demonstrates the same connected traces, metrics, and logs workflow as a conventional OpenTelemetry LGTM tutorial, while retaining ARIA's scalable pipeline and AI control plane.

## Request path

```text
client
  -> checkout-api /checkout
     -> W3C traceparent
     -> inventory-api /inventory/widget
  -> OTel gateway
     -> Tempo traces
     -> spanmetrics -> Prometheus
     -> Loki logs
     -> Kafka archive/replay path
  -> Grafana correlations
  -> ARIA investigation agents
```

Both services use FastAPI auto-instrumentation. The checkout service instruments its HTTP client, so the inventory server span joins the same distributed trace. JSON application logs include `trace_id` and `span_id`; Prometheus histograms include trace exemplars.

## Run locally on Kind

```bash
make kind-create
make k8s-bootstrap
make telemetry-deploy-local
make k8s-deploy-app
make port-forward
```

Install the Loki and Tempo Helm dependencies described under `telemetry/helm` before expecting backend queries to succeed.

Generate healthy traffic:

```bash
for i in {1..20}; do curl -s http://localhost:9000/checkout >/dev/null; done
```

Introduce a slow downstream dependency:

```bash
make generate-dependency-latency
for i in {1..20}; do curl -s http://localhost:9000/checkout >/dev/null; done
```

The checkout trace will show the inventory client/server spans consuming most of the request duration. Grafana's trace view links to logs sharing the trace ID, while the application dashboard shows the corresponding p99 increase.

## Automated proof

With checkout, Prometheus, Loki, and Tempo port-forwarded:

```bash
make verify-e2e-observability
```

The verifier creates one checkout, captures its trace ID, and fails unless it finds metrics, a log containing that trace ID, and the trace itself.

## Honest validation boundary

Static tests verify instrumentation and configuration contracts. The automated proof requires a running cluster and backends. Do not claim operational completion from source tests alone; retain the verifier output with the deployed revision.
