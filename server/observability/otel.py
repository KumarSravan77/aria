from __future__ import annotations


def setup_otel(app):
    import os
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        return
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
    if protocol == "http/protobuf":
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    else:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": os.getenv("OTEL_SERVICE_NAME", "aria"),
                "service.version": os.getenv("ARIA_VERSION", "2.0.0"),
                "deployment.environment": os.getenv("APP_ENV", "local"),
                "ai.observability.backend": os.getenv("AI_OBSERVABILITY_BACKEND", "otlp"),
            }
        )
    )
    trace.set_tracer_provider(provider)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    FastAPIInstrumentor.instrument_app(app)


def current_traceparent() -> str | None:
    try:
        from opentelemetry import trace

        context = trace.get_current_span().get_span_context()
        if not context.is_valid:
            return None
        flags = "01" if context.trace_flags.sampled else "00"
        return f"00-{context.trace_id:032x}-{context.span_id:016x}-{flags}"
    except ImportError:
        return None
