import os
import json
import logging
import random
import time
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram
from prometheus_client.openmetrics.exposition import generate_latest, CONTENT_TYPE_LATEST
import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TraceJsonFormatter(logging.Formatter):
    def format(self, record):
        span = trace.get_current_span()
        context = span.get_span_context()
        return json.dumps({
            "timestamp": time.time(),
            "severity": record.levelname,
            "service.name": "checkout-api",
            "message": record.getMessage(),
            "trace_id": format(context.trace_id, "032x") if context.is_valid else None,
            "span_id": format(context.span_id, "016x") if context.is_valid else None,
        })


def configure_telemetry():
    provider = TracerProvider(resource=Resource.create({
        "service.name": "checkout-api",
        "service.namespace": "aria-demo",
        "deployment.environment.name": os.getenv("ENVIRONMENT", "local"),
    }))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-gateway.telemetry.svc.cluster.local:4317"),
        insecure=True,
    )))
    trace.set_tracer_provider(provider)
    RequestsInstrumentor().instrument()


configure_telemetry()
logger = logging.getLogger("checkout-api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(TraceJsonFormatter())
logger.addHandler(handler)

app = FastAPI(title="Sample Checkout API")
FastAPIInstrumentor.instrument_app(app)
REQS = Counter("checkout_requests_total", "Total checkout requests", ["endpoint", "status"])
LAT = Histogram("checkout_request_duration_seconds", "Checkout request latency", ["endpoint"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "checkout-api"}

@app.get("/checkout")
def checkout():
    latency_ms = int(os.getenv("CHAOS_LATENCY_MS", "0"))
    error_rate = float(os.getenv("CHAOS_ERROR_RATE", "0"))
    start = time.time()
    inventory_url = os.getenv("INVENTORY_URL", "http://inventory-api:9100")
    try:
        inventory = requests.get(f"{inventory_url}/inventory/widget", timeout=3)
        inventory.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("inventory dependency failed: %s", exc)
        REQS.labels("/checkout", "503").inc()
        LAT.labels("/checkout").observe(time.time() - start, exemplar={"trace_id": format(trace.get_current_span().get_span_context().trace_id, "032x")})
        return Response(content='{"error":"inventory unavailable"}', media_type="application/json", status_code=503)
    if latency_ms > 0:
        time.sleep(latency_ms / 1000.0)
    if random.random() < error_rate:
        REQS.labels("/checkout", "500").inc()
        LAT.labels("/checkout").observe(time.time() - start, exemplar={"trace_id": format(trace.get_current_span().get_span_context().trace_id, "032x")})
        logger.error("checkout failed with simulated payment error")
        return Response(content='{"error":"simulated failure"}', media_type="application/json", status_code=500)
    REQS.labels("/checkout", "200").inc()
    LAT.labels("/checkout").observe(time.time() - start, exemplar={"trace_id": format(trace.get_current_span().get_span_context().trace_id, "032x")})
    order_id = random.randint(1000, 9999)
    trace_id = format(trace.get_current_span().get_span_context().trace_id, "032x")
    logger.info("checkout completed order_id=%s inventory_status=%s", order_id, inventory.status_code)
    return {"status": "success", "order_id": order_id, "trace_id": trace_id, "inventory": inventory.json()}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
