"""
Solar Operations OS — O&M Module: Database Models
Owns: MaintenancePlan, MaintenanceTask, Visit, VisitItem, Ticket, TicketEvent, SLAPolicy
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Interval,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin


class TicketStatus(StrEnum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(StrEnum):
    CORRECTIVE = "corrective"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    UPGRADE = "upgrade"


class VisitStatus(StrEnum):
    PLANNED = "planned"
    DISPATCHED = "dispatched"
    ARRIVED = "arrived"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"


# ── SLA Policy ────────────────────────────────────────────────────────────────
class SLAPolicy(Base, TenantMixin, TimestampMixin):
    __tablename__ = "sla_policy"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)
    first_response_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    escalation_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_sla_name"),
    )


# ── Maintenance Plan ──────────────────────────────────────────────────────────
class MaintenancePlan(Base, TenantMixin, TimestampMixin):
    __tablename__ = "maintenance_plan"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    tasks: Mapped[list[MaintenanceTask]] = relationship(
        "MaintenanceTask", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_maint_plan_project", "organization_id", "project_id"),
    )


# ── Maintenance Task ──────────────────────────────────────────────────────────
class MaintenanceTask(Base, TenantMixin, TimestampMixin):
    __tablename__ = "maintenance_task"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("maintenance_plan.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_duration_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    checklist_template: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    assigned_team_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    plan: Mapped[MaintenancePlan] = relationship("MaintenancePlan", back_populates="tasks")

    __table_args__ = (
        Index("ix_maint_task_plan", "plan_id"),
        Index("ix_maint_task_due", "organization_id", "next_due_date"),
    )


# ── Service Ticket ────────────────────────────────────────────────────────────
class Ticket(Base, TenantMixin, TimestampMixin):
    __tablename__ = "ticket"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number: Mapped[str] = mapped_column(String(50), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default=TicketCategory.CORRECTIVE)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=TicketPriority.MEDIUM)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=TicketStatus.OPEN)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reporter_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    assignee_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    sla_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sla_policy.id", ondelete="SET NULL"), nullable=True
    )
    first_response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    first_responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    affected_asset_ids: Mapped[list[str]] = mapped_column(ARRAY(String(36)), nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), nullable=False, default=list)

    ticket_events: Mapped[list[TicketEvent]] = relationship(
        "TicketEvent", back_populates="ticket", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "ticket_number", name="uq_ticket_number"),
        Index("ix_ticket_project", "organization_id", "project_id"),
        Index("ix_ticket_status", "organization_id", "status"),
        Index("ix_ticket_assignee", "assignee_user_id"),
    )


# ── Ticket Event Timeline ─────────────────────────────────────────────────────
class TicketEvent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "ticket_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ticket.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_meta: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="ticket_events")

    __table_args__ = (
        Index("ix_ticket_event_ticket", "ticket_id"),
    )


# ── Visit ─────────────────────────────────────────────────────────────────────
class Visit(Base, TenantMixin, TimestampMixin):
    __tablename__ = "visit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ticket.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    technician_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=VisitStatus.PLANNED)
    planned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    departed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    work_done_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parts_used: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    geo_location: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    photo_storage_keys: Mapped[list[str]] = mapped_column(ARRAY(String(512)), nullable=False, default=list)

    __table_args__ = (
        Index("ix_visit_project", "organization_id", "project_id"),
        Index("ix_visit_technician", "technician_user_id"),
    )
