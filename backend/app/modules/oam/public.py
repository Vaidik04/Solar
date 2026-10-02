"""
Solar Operations OS — O&M Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── SLA Policy ────────────────────────────────────────────────────────────────
class SLAPolicyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    priority: str = Field(..., max_length=50)
    first_response_hours: int = Field(..., ge=1)
    resolution_hours: int = Field(..., ge=1)
    escalation_hours: Optional[int] = None
    is_default: bool = False


class SLAPolicyOut(BaseModel):
    id: uuid.UUID
    name: str
    priority: str
    first_response_hours: int
    resolution_hours: int
    escalation_hours: Optional[int] = None
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Maintenance Tasks & Plans ─────────────────────────────────────────────────
class MaintenanceTaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    category: str = Field("preventive", max_length=50)
    frequency: str = Field("monthly", max_length=50)
    estimated_duration_hours: Optional[float] = None
    checklist_template: List[Dict[str, Any]] = Field(default_factory=list)
    assigned_team_id: Optional[uuid.UUID] = None
    next_due_date: Optional[date] = None


class MaintenanceTaskOut(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    title: str
    category: str
    frequency: str
    estimated_duration_hours: Optional[float] = None
    checklist_template: List[Dict[str, Any]]
    assigned_team_id: Optional[uuid.UUID] = None
    next_due_date: Optional[date] = None
    last_completed_date: Optional[date] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenancePlanCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    start_date: date
    end_date: Optional[date] = None
    tasks: List[MaintenanceTaskCreate] = Field(default_factory=list)


class MaintenancePlanOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    name: str
    is_active: bool
    start_date: date
    end_date: Optional[date] = None
    tasks: List[MaintenanceTaskOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Tickets & Ticket Events ───────────────────────────────────────────────────
class TicketEventOut(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    event_type: str
    description: str
    actor_user_id: Optional[uuid.UUID] = None
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    event_meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    title: str = Field(..., max_length=512)
    description: str = Field(..., min_length=5)
    category: str = Field("corrective", max_length=50)
    priority: str = Field("medium", max_length=50)
    assignee_user_id: Optional[uuid.UUID] = None
    affected_asset_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_user_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class TicketOut(BaseModel):
    id: uuid.UUID
    ticket_number: str
    project_id: uuid.UUID
    plant_id: str
    category: str
    priority: str
    status: str
    title: str
    description: str
    reporter_user_id: Optional[uuid.UUID] = None
    assignee_user_id: Optional[uuid.UUID] = None
    sla_policy_id: Optional[uuid.UUID] = None
    first_response_due_at: Optional[datetime] = None
    resolution_due_at: Optional[datetime] = None
    first_responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_asset_ids: List[str]
    tags: List[str]
    ticket_events: List[TicketEventOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Visits ────────────────────────────────────────────────────────────────────
class VisitCreate(BaseModel):
    project_id: uuid.UUID
    ticket_id: Optional[uuid.UUID] = None
    technician_user_id: Optional[uuid.UUID] = None
    planned_date: Optional[date] = None


class VisitUpdate(BaseModel):
    status: Optional[str] = None
    arrived_at: Optional[datetime] = None
    departed_at: Optional[datetime] = None
    work_done_summary: Optional[str] = None
    parts_used: Optional[List[Dict[str, Any]]] = None
    geo_location: Optional[Dict[str, Any]] = None
    photo_storage_keys: Optional[List[str]] = None


class VisitOut(BaseModel):
    id: uuid.UUID
    ticket_id: Optional[uuid.UUID] = None
    project_id: uuid.UUID
    technician_user_id: Optional[uuid.UUID] = None
    status: str
    planned_date: Optional[date] = None
    arrived_at: Optional[datetime] = None
    departed_at: Optional[datetime] = None
    work_done_summary: Optional[str] = None
    parts_used: List[Dict[str, Any]]
    geo_location: Optional[Dict[str, Any]] = None
    photo_storage_keys: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}
