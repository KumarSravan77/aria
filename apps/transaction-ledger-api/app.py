import json, logging, os, time
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

SERVICE="transaction-ledger-api"
provider=TracerProvider(resource=Resource.create({"service.name":SERVICE,"service.namespace":"mapletrust-bank"})); provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT","otel-gateway.telemetry.svc.cluster.local:4317"),insecure=True))); trace.set_tracer_provider(provider)
class Formatter(logging.Formatter):
    def format(self, record):
        ctx=trace.get_current_span().get_span_context(); return json.dumps({"timestamp":time.time(),"severity":record.levelname,"service.name":SERVICE,"message":record.getMessage(),"trace_id":format(ctx.trace_id,"032x") if ctx.is_valid else None,"span_id":format(ctx.span_id,"016x") if ctx.is_valid else None})
logger=logging.getLogger(SERVICE); logger.setLevel(logging.INFO); handler=logging.StreamHandler(); handler.setFormatter(Formatter()); logger.addHandler(handler)
app=FastAPI(title="MapleTrust Transaction Ledger API"); FastAPIInstrumentor.instrument_app(app)
@app.get("/health")
def health(): return {"status":"ok","service":SERVICE}
@app.post("/entries")
def entry(payload: dict):
    if os.getenv("LEDGER_FAILURE","false").lower()=="true": logger.error("ledger write failed transaction_id=%s",payload.get("transaction_id")); raise HTTPException(503,"ledger unavailable")
    logger.info("ledger entry committed transaction_id=%s",payload.get("transaction_id")); return {"committed":True}
