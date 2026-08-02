import json, logging, os, random, time
import requests
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram
from prometheus_client.openmetrics.exposition import generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE = "banking-api"
provider = TracerProvider(resource=Resource.create({"service.name": SERVICE, "service.namespace": "mapletrust-bank"}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-gateway.telemetry.svc.cluster.local:4317"), insecure=True)))
trace.set_tracer_provider(provider)
RequestsInstrumentor().instrument()

class Formatter(logging.Formatter):
    def format(self, record):
        ctx = trace.get_current_span().get_span_context()
        return json.dumps({"timestamp": time.time(), "severity": record.levelname, "service.name": SERVICE, "message": record.getMessage(), "trace_id": format(ctx.trace_id, "032x") if ctx.is_valid else None, "span_id": format(ctx.span_id, "016x") if ctx.is_valid else None})

logger = logging.getLogger(SERVICE); logger.setLevel(logging.INFO)
handler = logging.StreamHandler(); handler.setFormatter(Formatter()); logger.addHandler(handler)
app = FastAPI(title="MapleTrust Digital Banking API")
FastAPIInstrumentor.instrument_app(app)
REQS = Counter("banking_transactions_total", "Banking transactions", ["status"])
LAT = Histogram("banking_transaction_duration_seconds", "Transaction latency")

@app.get("/health")
def health(): return {"status": "ok", "service": SERVICE}

@app.post("/transactions")
def transaction(amount: float = 125.0, account_id: str = "demo-account"):
    started = time.time(); fraud_url = os.getenv("FRAUD_URL", "http://fraud-detection-api:9300"); ledger_url = os.getenv("LEDGER_URL", "http://transaction-ledger-api:9400")
    try:
        fraud = requests.post(f"{fraud_url}/score", json={"amount": amount, "account_id": account_id}, timeout=4); fraud.raise_for_status()
        if fraud.json()["decision"] == "decline":
            REQS.labels("declined").inc(); logger.warning("transaction declined account=%s amount=%s", account_id, amount)
            return Response(content=json.dumps({"status": "declined", "reason": "risk policy"}), media_type="application/json", status_code=422)
        transaction_id = f"txn-{random.randint(100000, 999999)}"
        ledger = requests.post(f"{ledger_url}/entries", json={"transaction_id": transaction_id, "amount": amount}, timeout=4); ledger.raise_for_status()
    except requests.RequestException as exc:
        REQS.labels("failed").inc(); logger.exception("transaction dependency failure: %s", exc)
        return Response(content='{"status":"failed"}', media_type="application/json", status_code=503)
    ctx = trace.get_current_span().get_span_context(); trace_id = format(ctx.trace_id, "032x")
    LAT.observe(time.time() - started, exemplar={"trace_id": trace_id}); REQS.labels("approved").inc()
    logger.info("transaction approved transaction_id=%s amount=%s", transaction_id, amount)
    return {"status": "approved", "transaction_id": transaction_id, "trace_id": trace_id}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
