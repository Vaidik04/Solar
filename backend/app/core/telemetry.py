"""
Solar Operations OS — Structured Logging and OpenTelemetry Setup
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None  # type: ignore[assignment,misc]

try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except ImportError:
    SQLAlchemyInstrumentor = None  # type: ignore[assignment,misc]

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from prometheus_client import Counter, Histogram, make_asgi_app

from app.core.config import get_settings

# ── Prometheus Metrics ────────────────────────────────────────────────────────
http_requests_total = Counter(
    "solar_os_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "solar_os_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

db_query_duration_seconds = Histogram(
    "solar_os_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

outbox_events_processed = Counter(
    "solar_os_outbox_events_processed_total",
    "Outbox events processed",
    ["event_type", "status"],
)

compliance_runs_total = Counter(
    "solar_os_compliance_runs_total",
    "Compliance engine runs",
    ["result"],
)

# ── Sensitive Field Filter ────────────────────────────────────────────────────
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "secret",
        "api_key",
        "access_token",
        "refresh_token",
        "authorization",
        "jwt",
        "private_key",
        "consumer_number",
        "aadhaar",
        "totp_secret",
        "backup_code",
        "hmac_key",
        "encryption_key",
    }
)


def _redact_sensitive(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that redacts sensitive fields."""
    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in _SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
    return event_dict


# ── Structlog Configuration ───────────────────────────────────────────────────
def setup_logging() -> None:
    settings = get_settings()

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _redact_sensitive,
    ]

    if settings.LOG_FORMAT == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard library logging → structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )


# ── OpenTelemetry Setup ───────────────────────────────────────────────────────
def setup_tracing() -> None:
    settings = get_settings()

    resource = Resource.create(
        {
            "service.name": "solar-operations-os",
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.APP_ENV,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.OTEL_ENDPOINT and OTLPSpanExporter is not None:
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_ENDPOINT, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        # In development, export to console at DEBUG level
        if settings.DEBUG:
            provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

    trace.set_tracer_provider(provider)


def setup_instrumentation(app: Any) -> None:
    """Instrument FastAPI and SQLAlchemy for automatic tracing."""
    if FastAPIInstrumentor is not None:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="/health,/ready,/metrics",
        )
    if SQLAlchemyInstrumentor is not None:
        SQLAlchemyInstrumentor().instrument()



def get_tracer() -> trace.Tracer:
    return trace.get_tracer("solar-operations-os")


# ── Request Context Logging ───────────────────────────────────────────────────
def bind_request_context(
    request_id: str,
    tenant_id: str | None,
    user_id: str | None,
) -> None:
    """Bind request-level context to structlog's context vars."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        tenant_id=tenant_id or "anonymous",
        user_id=user_id or "anonymous",
    )


# ── Prometheus ASGI App ───────────────────────────────────────────────────────
metrics_app = make_asgi_app()
