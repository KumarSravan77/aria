import json
import logging
import os
import time
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram
from prometheus_client.openmetrics.exposition import generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TraceJsonFormatter(logging.Formatter):
    def format(self, record):
        context = trace.get_current_span().get_span_context()
        return json.dumps({
            "timestamp": time.time(), "severity": record.levelname,
            "service.name": "inventory-api", "message": record.getMessage(),
            "trace_id": format(context.trace_id, "032x") if context.is_valid else None,
            "span_id": format(context.span_id, "016x") if context.is_valid else None,
        })


provider = TracerProvider(resource=Resource.create({"service.name": "inventory-api", "service.namespace": "aria-demo"}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-gateway.telemetry.svc.cluster.local:4317"), insecure=True,
)))
trace.set_tracer_provider(provider)
logger = logging.getLogger("inventory-api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(TraceJsonFormatter())
logger.addHandler(handler)

app = FastAPI(title="ARIA Inventory API")
FastAPIInstrumentor.instrument_app(app)
REQS = Counter("inventory_requests_total", "Inventory requests", ["status"])
LAT = Histogram("inventory_request_duration_seconds", "Inventory latency")


@app.get("/health")
def health():
    return {"status": "ok", "service": "inventory-api"}


@app.get("/inventory/{sku}")
def inventory(sku: str):
    start = time.time()
    delay_ms = int(os.getenv("INVENTORY_DELAY_MS", "0"))
    if delay_ms:
        time.sleep(delay_ms / 1000)
    elapsed = time.time() - start
    context = trace.get_current_span().get_span_context()
    LAT.observe(elapsed, exemplar={"trace_id": format(context.trace_id, "032x")})
    REQS.labels("200").inc()
    logger.info("inventory lookup sku=%s delay_ms=%s", sku, delay_ms)
    return {"sku": sku, "available": 42, "delay_ms": delay_ms}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
