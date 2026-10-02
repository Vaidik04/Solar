"""
Solar Operations OS — O&M Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TicketCreated:
    event_type: str = field(default="oam.ticket.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    ticket_id: uuid.UUID = uuid.UUID(int=0)
    ticket_number: str = ""
    priority: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TicketAssigned:
    event_type: str = field(default="oam.ticket.assigned", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    ticket_id: uuid.UUID = uuid.UUID(int=0)
    assignee_user_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TicketStatusChanged:
    event_type: str = field(default="oam.ticket.status_changed", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    ticket_id: uuid.UUID = uuid.UUID(int=0)
    from_status: str = ""
    to_status: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VisitScheduled:
    event_type: str = field(default="oam.visit.scheduled", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    visit_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    technician_user_id: uuid.UUID | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MaintenanceTaskCompleted:
    event_type: str = field(default="oam.maintenance_task.completed", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    task_id: uuid.UUID = uuid.UUID(int=0)
    plan_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
