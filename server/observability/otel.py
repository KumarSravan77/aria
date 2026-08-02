def setup_otel(app):
    import os
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    trace.set_tracer_provider(TracerProvider())
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
    FastAPIInstrumentor.instrument_app(app)
