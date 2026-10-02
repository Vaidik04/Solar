"""
Solar Operations OS — RFC 7807 Problem Details Error Model
Uniform error responses across all endpoints.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# ── Problem Details Schema ────────────────────────────────────────────────────
class FieldError(BaseModel):
    field: str
    code: str
    message: str


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details — https://www.rfc-editor.org/rfc/rfc7807"""

    type: str  # URI identifying the problem type
    title: str  # Short human-readable summary
    status: int  # HTTP status code
    detail: str | None = None  # Specific occurrence description
    instance: str | None = None  # URI of the specific resource
    trace_id: str | None = None  # OpenTelemetry trace ID
    errors: list[FieldError] | None = None  # Field-level validation errors

    model_config = {"extra": "allow"}  # Allow domain-specific extensions


# ── Error Base URL ────────────────────────────────────────────────────────────
_ERROR_BASE = "https://errors.solar-os.example.com"


def problem(
    *,
    status_code: int,
    error_code: str,
    title: str,
    detail: str | None = None,
    instance: str | None = None,
    errors: list[FieldError] | None = None,
    **extra: Any,
) -> ProblemDetail:
    return ProblemDetail(
        type=f"{_ERROR_BASE}/{error_code}",
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        errors=errors,
        **extra,
    )


# ── Domain Exceptions ─────────────────────────────────────────────────────────
class SolarOSError(Exception):
    """Base exception for all domain errors."""

    status_code: int = 500
    error_code: str = "internal-error"
    title: str = "Internal server error"

    def __init__(self, detail: str | None = None, **extra: Any) -> None:
        self.detail = detail
        self.extra = extra
        super().__init__(detail)

    def to_problem(self, instance: str | None = None) -> ProblemDetail:
        return problem(
            status_code=self.status_code,
            error_code=self.error_code,
            title=self.title,
            detail=self.detail,
            instance=instance,
            **self.extra,
        )


class NotFoundError(SolarOSError):
    status_code = 404
    error_code = "not-found"
    title = "Resource not found"


class ForbiddenError(SolarOSError):
    status_code = 403
    error_code = "forbidden"
    title = "Access denied"


class UnauthorizedError(SolarOSError):
    status_code = 401
    error_code = "unauthenticated"
    title = "Authentication required"


class ConflictError(SolarOSError):
    status_code = 409
    error_code = "state-conflict"
    title = "State conflict"


class OptimisticConcurrencyError(SolarOSError):
    status_code = 409
    error_code = "optimistic-concurrency"
    title = "Concurrent modification conflict"


class IdempotencyConflictError(SolarOSError):
    status_code = 409
    error_code = "duplicate-idempotency"
    title = "Idempotency key reused with different payload"


class ValidationError(SolarOSError):
    status_code = 422
    error_code = "validation-error"
    title = "Validation failed"


class RateLimitError(SolarOSError):
    status_code = 429
    error_code = "rate-limited"
    title = "Rate limit exceeded"


class WorkflowTransitionError(SolarOSError):
    status_code = 409
    error_code = "invalid-transition"
    title = "Workflow transition not allowed"

    def __init__(
        self,
        detail: str | None = None,
        blockers: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.extra = {"blockers": blockers or []}


class TenantContextError(SolarOSError):
    """Raised when tenant context is missing (programming error, not user error)."""

    status_code = 500
    error_code = "tenant-context-missing"
    title = "Tenant context not established"


# ── FastAPI Exception Handlers ────────────────────────────────────────────────
def _get_trace_id(request: Request) -> str | None:
    """Extract OpenTelemetry trace ID from request if available."""
    from opentelemetry import trace

    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return None


def _problem_response(
    request: Request, prob: ProblemDetail
) -> JSONResponse:
    import orjson

    prob.instance = str(request.url.path)
    prob.trace_id = _get_trace_id(request)
    return JSONResponse(
        content=orjson.loads(prob.model_dump_json(exclude_none=True)),
        status_code=prob.status,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""

    @app.exception_handler(SolarOSError)
    async def solar_os_error_handler(
        request: Request, exc: SolarOSError
    ) -> JSONResponse:
        return _problem_response(request, exc.to_problem())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        field_errors = [
            FieldError(
                field=".".join(str(loc) for loc in err["loc"][1:]) or "body",
                code=err["type"],
                message=err["msg"],
            )
            for err in exc.errors()
        ]
        prob = problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="validation-error",
            title="Request validation failed",
            detail="One or more fields failed validation.",
            errors=field_errors,
        )
        return _problem_response(request, prob)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        import structlog

        logger = structlog.get_logger()
        logger.exception("unhandled_exception", exc_info=exc)

        from app.core.config import get_settings

        prob = problem(
            status_code=500,
            error_code="internal-error",
            title="An unexpected error occurred",
            detail="Please try again. If the problem persists, contact support."
            if get_settings().is_production
            else str(exc),
        )
        return _problem_response(request, prob)
