"""
Solar Operations OS — Project & Workflow Engine: Database Models
Owns: Project, Application, WorkflowDefinition, WorkflowInstance, StageHistory, WorkflowTransitionOverride
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, VersionMixin


# ── Standard Lifecycle Stages ─────────────────────────────────────────────────
class ProjectStage(StrEnum):
    LEAD = "lead"
    SITE_SURVEY = "site_survey"
    ENGINEERING_DESIGN = "engineering_design"
    PROPOSAL_ACCEPTED = "proposal_accepted"
    DISCOM_APPLICATION = "discom_application"
    PROCUREMENT = "procurement"
    INSTALLATION = "installation"
    TESTING_INSPECTION = "testing_inspection"
    WCR_GENERATION = "wcr_generation"
    COMMISSIONING = "commissioning"
    HANDOVER = "handover"
    OAM_ACTIVE = "oam_active"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiscomAppStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    FEASIBILITY_APPROVED = "feasibility_approved"
    WORK_COMMENCEMENT_APPROVED = "work_commencement_approved"
    INSPECTION_PENDING = "inspection_pending"
    METERING_APPROVED = "metering_approved"
    REJECTED = "rejected"


# ── Project ───────────────────────────────────────────────────────────────────
class Project(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)  # SOL-MH-000124 (Digital Passport ID)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customer.id", ondelete="RESTRICT"), nullable=False
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branch.id", ondelete="SET NULL"), nullable=True
    )
    manager_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    # Capacity & System Specs
    capacity_kw_dc: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_kw_ac: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    estimated_annual_kwh: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)

    # Workflow & Lifecycle State
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False, default=ProjectStage.LEAD)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ProjectStatus.ACTIVE)
    stage_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    target_commissioning_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_commissioning_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata & Custom Fields
    project_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    applications: Mapped[list[Application]] = relationship("Application", back_populates="project", cascade="all, delete-orphan")
    stage_histories: Mapped[list[StageHistory]] = relationship("StageHistory", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "plant_id", name="uq_project_org_plant_id"),
        Index("ix_project_org_stage", "organization_id", "current_stage"),
        Index("ix_project_org_customer", "organization_id", "customer_id"),
        Index("ix_project_org_site", "organization_id", "site_id"),
    )


# ── DISCOM Interconnection Application ─────────────────────────────────────────
class Application(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "application"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    discom_name: Mapped[str] = mapped_column(String(100), nullable=False)
    application_number: Mapped[str] = mapped_column(String(100), nullable=False)
    consumer_number: Mapped[str] = mapped_column(String(100), nullable=False)
    feeder_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dt_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Distribution Transformer Code

    applied_capacity_kw: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sanctioned_capacity_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DiscomAppStatus.DRAFT)

    submission_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discom_fee_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    discom_fee_receipt_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="applications")

    __table_args__ = (
        Index("ix_app_project", "project_id"),
        Index("ix_app_org_status", "organization_id", "status"),
        Index("ix_app_discom_app_num", "organization_id", "discom_name", "application_number"),
    )


# ── Workflow Definition ───────────────────────────────────────────────────────
class WorkflowDefinition(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "workflow_definition"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "DEFAULT_ROOFTOP_V1"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    definition_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Declarative stage DAG, guard rules, and SLA definitions in hours
    stages_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    transitions_config: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", "definition_version", name="uq_workflow_org_code_ver"),
    )


# ── Stage History (Audit & SLA Tracking) ──────────────────────────────────────
class StageHistory(Base, TenantMixin, TimestampMixin):
    __tablename__ = "stage_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    from_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    duration_in_stage_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    transition_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    guard_results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    project: Mapped[Project] = relationship("Project", back_populates="stage_histories")

    __table_args__ = (
        Index("ix_stage_hist_project", "project_id"),
        Index("ix_stage_hist_org_transition", "organization_id", "to_stage"),
    )


# ── Workflow Transition Override ──────────────────────────────────────────────
class WorkflowTransitionOverride(Base, TenantMixin, TimestampMixin):
    """
    Records human-authorized bypasses of workflow guards (e.g. fast-tracking urgent installs).
    Requires explicit justification and approval for full audit trail.
    """
    __tablename__ = "workflow_transition_override"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    from_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    failed_guards: Mapped[dict] = mapped_column(JSONB, nullable=False)
