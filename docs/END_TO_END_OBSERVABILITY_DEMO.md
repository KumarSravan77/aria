# End-to-End Observability Demo

This scenario uses **MapleTrust Bank**, a fictional Canadian financial institution. It is not affiliated with CIBC, RBC, or any real bank. It demonstrates the same connected traces, metrics, and logs workflow as a conventional OpenTelemetry LGTM tutorial while retaining ARIA's scalable pipeline and AI control plane.

## Request path

```text
client
  -> banking-api /transactions
     -> W3C traceparent -> fraud-detection-api /score
     -> W3C traceparent -> transaction-ledger-api /entries
  -> OTel gateway
     -> Tempo traces
     -> spanmetrics -> Prometheus
     -> Loki logs
     -> Kafka archive/replay path
  -> Grafana correlations
  -> ARIA investigation agents
```

All three services use FastAPI auto-instrumentation. The banking API instruments its HTTP client, so fraud and ledger server spans join the same distributed trace. JSON logs include `trace_id` and `span_id`; Prometheus histograms include trace exemplars. Payloads avoid storing personal financial information.

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
for i in {1..20}; do curl -s -X POST 'http://localhost:9200/transactions?amount=125' >/dev/null; done
```

Introduce a slow downstream dependency:

```bash
make generate-dependency-latency
for i in {1..20}; do curl -s -X POST 'http://localhost:9200/transactions?amount=125' >/dev/null; done
```

The banking trace will show fraud scoring consuming most of the request duration. A transaction above the configured threshold demonstrates a policy decline; `make generate-ledger-failure` demonstrates a downstream availability failure. Grafana links traces to logs sharing the trace ID while the dashboard shows the corresponding p99 and error-rate changes.

## Automated proof

With checkout, Prometheus, Loki, and Tempo port-forwarded:

```bash
make verify-e2e-observability
```

The verifier creates one banking transaction, captures its trace ID, and fails unless it finds metrics, a log containing that trace ID, and the trace itself.

## Honest validation boundary

Static tests verify instrumentation and configuration contracts. The automated proof requires a running cluster and backends. Do not claim operational completion from source tests alone; retain the verifier output with the deployed revision.
