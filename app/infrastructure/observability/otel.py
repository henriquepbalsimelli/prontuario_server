from __future__ import annotations

import logging

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.infrastructure.settings import Settings

logger = logging.getLogger(__name__)


def _parse_otlp_headers(raw_headers: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not raw_headers.strip():
        return headers

    for pair in raw_headers.split(","):
        key, sep, value = pair.partition("=")
        if not sep:
            continue

        clean_key = key.strip()
        clean_value = value.strip()
        if clean_key and clean_value:
            headers[clean_key] = clean_value

    return headers


def configure_observability(
    *,
    app: FastAPI,
    settings: Settings,
    engine: AsyncEngine,
) -> None:
    if not settings.otel_enabled:
        logger.info("OpenTelemetry disabled by configuration")
        return

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.exception(
            "OpenTelemetry dependencies are missing. Install project dependencies before enabling OTEL."
        )
        return

    headers = _parse_otlp_headers(settings.otel_exporter_otlp_headers)

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )

    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
                insecure=settings.otel_exporter_otlp_insecure,
                headers=headers,
                timeout=settings.otel_exporter_otlp_timeout_seconds,
            )
        )
    )
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=settings.otel_exporter_otlp_insecure,
            headers=headers,
            timeout=settings.otel_exporter_otlp_timeout_seconds,
        ),
        export_interval_millis=settings.otel_metric_export_interval_ms,
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    excluded_urls = settings.otel_excluded_urls
    FastAPIInstrumentor().instrument_app(app, excluded_urls=excluded_urls)

    sqlalchemy_instrumentor = SQLAlchemyInstrumentor()
    if not sqlalchemy_instrumentor.is_instrumented_by_opentelemetry:
        sqlalchemy_instrumentor.instrument(engine=engine.sync_engine)

    httpx_instrumentor = HTTPXClientInstrumentor()
    if not httpx_instrumentor.is_instrumented_by_opentelemetry:
        httpx_instrumentor.instrument()

    logger.info(
        "OpenTelemetry configured",
        extra={
            "otel_endpoint": settings.otel_exporter_otlp_endpoint,
            "otel_excluded_urls": excluded_urls,
        },
    )
