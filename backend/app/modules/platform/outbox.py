"""
Solar Operations OS — Transactional Outbox Dispatcher (ADR-003)
Polls for pending outbox events and dispatches to registered handlers.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.core.telemetry import outbox_events_processed
from app.modules.platform.models import OutboxEvent, OutboxStatus

logger = structlog.get_logger()

# ── Handler Registry ──────────────────────────────────────────────────────────
EventHandler = Callable[[dict[str, Any]], Awaitable[None]]
_handlers: dict[str, list[EventHandler]] = {}


def register_handler(event_type: str, handler: EventHandler) -> None:
    """Register a handler for a specific event type. Multiple handlers allowed."""
    _handlers.setdefault(event_type, []).append(handler)


def register_handlers(event_type: str, *handlers: EventHandler) -> None:
    for h in handlers:
        register_handler(event_type, h)


# ── Outbox Publisher ──────────────────────────────────────────────────────────
async def publish_outbox_event(
    *,
    db: AsyncSession,
    org_id: uuid.UUID,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    deliver_after: datetime | None = None,
) -> OutboxEvent:
    """
    Write an outbox event atomically within the current transaction.
    Called by domain services before committing state changes.
    """
    event = OutboxEvent(
        id=uuid.uuid4(),
        organization_id=org_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        status=OutboxStatus.PENDING,
        deliver_after=deliver_after,
    )
    db.add(event)
    return event


# ── Dispatcher ────────────────────────────────────────────────────────────────
async def dispatch_pending_events(batch_size: int = 100) -> int:
    """
    Poll for pending outbox events and dispatch to handlers.
    Uses SKIP LOCKED to allow multiple workers without conflicts.
    Returns number of events processed.
    """
    settings = get_settings()
    factory = get_session_factory()
    processed = 0

    async with factory() as db:
        # Lock and fetch pending events
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status == OutboxStatus.PENDING,
                (OutboxEvent.deliver_after.is_(None)) | (OutboxEvent.deliver_after <= now),
            )
            .order_by(OutboxEvent.created_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        events = result.scalars().all()

        for event in events:
            success = await _process_event(event, settings, db)
            if success:
                processed += 1

        await db.commit()

    return processed


async def _process_event(
    event: OutboxEvent,
    settings: Any,
    db: AsyncSession,
) -> bool:
    handlers = _handlers.get(event.event_type, [])
    if not handlers:
        # No handlers registered — silently mark as delivered
        event.status = OutboxStatus.DELIVERED
        event.delivered_at = datetime.now(timezone.utc)
        outbox_events_processed.labels(event_type=event.event_type, status="no_handler").inc()
        return True

    event.attempts += 1
    errors: list[str] = []

    for handler in handlers:
        try:
            await handler(event.payload)
        except Exception as exc:
            errors.append(f"{handler.__name__}: {exc}")
            logger.warning(
                "outbox_handler_failed",
                event_id=str(event.id),
                event_type=event.event_type,
                handler=handler.__name__,
                error=str(exc),
            )

    if errors:
        event.last_error = "; ".join(errors)
        if event.attempts >= settings.OUTBOX_MAX_DELIVERY_ATTEMPTS:
            event.status = OutboxStatus.DEAD
            outbox_events_processed.labels(event_type=event.event_type, status="dead").inc()
            logger.error(
                "outbox_event_dead",
                event_id=str(event.id),
                event_type=event.event_type,
                attempts=event.attempts,
            )
        else:
            event.status = OutboxStatus.PENDING  # keep for retry
            outbox_events_processed.labels(event_type=event.event_type, status="failed").inc()
        return False
    else:
        event.status = OutboxStatus.DELIVERED
        event.delivered_at = datetime.now(timezone.utc)
        outbox_events_processed.labels(event_type=event.event_type, status="delivered").inc()
        return True


# ── Background Poller ─────────────────────────────────────────────────────────
async def run_outbox_poller() -> None:
    """Long-running background task that polls and dispatches outbox events."""
    settings = get_settings()
    logger.info("outbox_poller_started", interval=settings.OUTBOX_POLL_INTERVAL_SECONDS)
    while True:
        try:
            count = await dispatch_pending_events()
            if count > 0:
                logger.debug("outbox_batch_processed", count=count)
        except Exception as exc:
            logger.exception("outbox_poller_error", error=str(exc))
        await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)
