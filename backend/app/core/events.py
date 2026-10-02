"""
Solar Operations OS — Domain Event Bus & Outbox Bridge
Provides:
- Base DomainEvent class
- In-process event dispatcher with async subscribers
- Outbox event publisher for cross-module async decoupling (ADR-003)
"""
from __future__ import annotations

import asyncio
import inspect
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Type

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.platform.models import OutboxEvent

logger = structlog.get_logger()

# Handler type: async function taking an event instance
EventHandler = Callable[[Any], Awaitable[None]]


@dataclass
class DomainEvent:
    """Base class for all domain events across modules."""

    organization_id: uuid.UUID
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_type(self) -> str:
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Format datetimes and UUIDs to ISO/string
        for k, v in data.items():
            if isinstance(v, uuid.UUID):
                data[k] = str(v)
            elif isinstance(v, datetime):
                data[k] = v.isoformat()
        return data


class EventBus:
    """
    In-process async event bus.
    Subscribers register for specific event types.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def subscribe(self, event_cls: Type[DomainEvent], handler: EventHandler) -> None:
        if event_cls not in self._handlers:
            self._handlers[event_cls] = []
        self._handlers[event_cls].append(handler)
        logger.debug("event_handler_subscribed", event_type=event_cls.__name__, handler=handler.__name__)

    async def publish(self, event: DomainEvent) -> None:
        """Publishes an event in-process to all registered subscribers."""
        event_cls = type(event)
        handlers = self._handlers.get(event_cls, [])
        if not handlers:
            return

        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(
                    "event_handler_failed",
                    event_type=event.event_type,
                    event_id=str(event.event_id),
                    handler=handler.__name__,
                    error=str(e),
                    exc_info=True,
                )

    async def emit_to_outbox(self, session: AsyncSession, event: DomainEvent) -> OutboxEvent:
        """
        Persists the event to the transactional outbox table in the same DB transaction.
        Guarantees at-least-once delivery to other modules and external queues.
        """
        payload = event.to_dict()
        outbox_entry = OutboxEvent(
            id=event.event_id,
            organization_id=event.organization_id,
            event_type=event.event_type,
            payload=payload,
        )
        session.add(outbox_entry)
        logger.info(
            "outbox_event_buffered",
            event_type=event.event_type,
            event_id=str(event.event_id),
            organization_id=str(event.organization_id),
        )
        return outbox_entry


# Global singleton event bus
event_bus = EventBus()
