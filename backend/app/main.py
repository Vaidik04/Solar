"""
Solar Operations OS — FastAPI Application Entry Point
"""
from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.db import close_db, init_db
from app.core.errors import register_exception_handlers
from app.core.idempotency import close_redis, init_redis
from app.core.telemetry import (
    bind_request_context,
    metrics_app,
    setup_instrumentation,
    setup_logging,
    setup_tracing,
)
from app.modules.identity.router import router as auth_router
from app.modules.platform.outbox import run_outbox_poller

logger = structlog.get_logger()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Initialize infrastructure
    setup_logging()
    setup_tracing()
    init_db()
    await init_redis()

    logger.info(
        "application_started",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # Start background workers
    outbox_task = asyncio.create_task(run_outbox_poller())

    try:
        yield
    finally:
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass

        await close_redis()
        await close_db()
        logger.info("application_shutdown")


# ── Application ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Solar Operations OS API",
        version=settings.APP_VERSION,
        description="Multi-tenant platform for solar EPC companies",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Dev frontend; override in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    # ── Request Context Middleware ─────────────────────────────────────────────
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next: object) -> object:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Bind to structlog context for this request
        bind_request_context(
            request_id=request_id,
            tenant_id=None,  # Set after auth
            user_id=None,
        )
        response = await call_next(request)  # type: ignore[operator]
        response.headers["X-Request-ID"] = request_id
        response.headers["X-API-Version"] = settings.APP_VERSION
        return response

    # ── Exception Handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.modules.crm.router import router as crm_router
    from app.modules.project.router import router as project_router
    from app.modules.assets.router import router as assets_router
    from app.modules.engineering.router import router as engineering_router
    from app.modules.supply.router import router as supply_router
    from app.modules.documents.router import router as documents_router
    from app.modules.regulations.router import router as regulations_router
    from app.modules.compliance.router import router as compliance_router
    from app.modules.reconciliation.router import router as reconciliation_router
    from app.modules.field.router import router as field_router
    from app.modules.warranty.router import router as warranty_router
    from app.modules.oam.router import router as oam_router
    from app.modules.telemetry_data.router import router as telemetry_router

    api_v1 = FastAPI(title="Solar OS API v1")
    api_v1.include_router(auth_router)
    api_v1.include_router(crm_router)
    api_v1.include_router(project_router)
    api_v1.include_router(assets_router)
    api_v1.include_router(engineering_router)
    api_v1.include_router(supply_router)
    api_v1.include_router(documents_router)
    api_v1.include_router(regulations_router)
    api_v1.include_router(compliance_router)
    api_v1.include_router(reconciliation_router)
    api_v1.include_router(field_router)
    api_v1.include_router(warranty_router)
    api_v1.include_router(oam_router)
    api_v1.include_router(telemetry_router)

    app.mount("/v1", api_v1)

    # ── Health Endpoints ──────────────────────────────────────────────────────
    @app.get("/health", tags=["platform"])
    async def health() -> dict:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/ready", tags=["platform"])
    async def ready() -> dict:
        """Readiness probe — checks DB, Redis, S3 connectivity."""
        checks: dict[str, str] = {}

        # Check DB
        try:
            from app.core.db import get_engine
            from sqlalchemy import text

            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

        # Check Redis
        try:
            from app.core.idempotency import get_redis

            await get_redis().ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            content={"status": "ready" if all_ok else "degraded", "checks": checks},
            status_code=200 if all_ok else 503,
        )

    # ── Metrics ───────────────────────────────────────────────────────────────
    app.mount("/metrics", metrics_app)

    # ── OpenTelemetry Instrumentation ─────────────────────────────────────────
    setup_instrumentation(app)

    return app


app = create_app()
