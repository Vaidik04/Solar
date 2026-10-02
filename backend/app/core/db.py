"""
Solar Operations OS — Database Layer
- Async SQLAlchemy engine with connection pooling
- Tenant context propagation via contextvars
- RLS activation helper (sets app.current_tenant on each session)
- Base model with common columns
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import DateTime, String, event, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import get_settings

# ── Tenant Context Variable ───────────────────────────────────────────────────
# Set at the start of every request; read by the RLS activation helper.
# This is the authoritative tenant context — never set from user input.
_current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar(
    "current_tenant_id", default=None
)


def get_current_tenant_id() -> uuid.UUID | None:
    return _current_tenant_id.get()


def set_current_tenant_id(tenant_id: uuid.UUID) -> None:
    _current_tenant_id.set(tenant_id)


def clear_current_tenant_id() -> None:
    _current_tenant_id.set(None)


# ── Engine Factory ────────────────────────────────────────────────────────────
def create_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or str(settings.DATABASE_URL)
    # Convert sync DSN to async (postgresql:// → postgresql+asyncpg://)
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    url = url.replace("postgres://", "postgresql+asyncpg://")

    engine = create_async_engine(
        url,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,
        echo=settings.DEBUG,
        # Use orjson for JSON serialization in asyncpg
        json_serializer=_json_serializer,
        json_deserializer=_json_deserializer,
    )
    return engine


def _json_serializer(obj: Any) -> str:
    import orjson

    return orjson.dumps(obj).decode()


def _json_deserializer(s: str) -> Any:
    import orjson

    return orjson.loads(s)


# ── Global Engine and Session Factory ────────────────────────────────────────
# Initialized on application startup via lifespan
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str | None = None) -> None:
    global _engine, _session_factory
    _engine = create_engine(database_url)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


# ── RLS Session Factory ───────────────────────────────────────────────────────
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async session with RLS tenant context activated.

    This is the ONLY way application code should get a database session.
    The tenant ID is read from the context variable (set by auth middleware),
    never from user input.
    """
    factory = get_session_factory()
    async with factory() as session:
        tenant_id = get_current_tenant_id()
        if tenant_id is not None:
            # Set PostgreSQL session-level variable for RLS policies
            await session.execute(
                text("SET LOCAL app.current_tenant = :tid"),
                {"tid": str(tenant_id)},
            )
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            # Clear the setting on session close (belt-and-suspenders)
            try:
                await session.execute(text("RESET app.current_tenant"))
            except Exception:
                pass  # Session may already be closed


async def get_privileged_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a session WITHOUT RLS (for platform admin operations, migrations).
    Requires explicit privilege escalation — logs usage.
    """
    import structlog

    logger = structlog.get_logger()
    logger.warning(
        "privileged_session_used",
        hint="This bypasses RLS — ensure this is intentional",
    )
    factory = get_session_factory()
    async with factory() as session:
        yield session


# ── Base Model ────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    SQLAlchemy declarative base with common audit columns.
    All tables inherit from this.
    """

    # SQLAlchemy type annotation mapping
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete support."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )


class VersionMixin:
    """Mixin for optimistic concurrency control via version column."""

    version: Mapped[int] = mapped_column(default=1, nullable=False)


class TenantMixin:
    """
    Mixin for all tenant-scoped tables.
    organization_id is the RLS anchor — must appear in every query predicate.
    """

    organization_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False, index=True
    )
