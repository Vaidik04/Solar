"""
Solar Operations OS — Field Module: Database Models
Owns: Meter, MeterTest, InspectionTemplate, Inspection, InspectionItem, WCR, CommissioningRecord
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin, VersionMixin


class MeterType(StrEnum):
    NET_METER = "net_meter"
    GENERATION_METER = "generation_meter"
    BI_DIRECTIONAL = "bi_directional"


class InspectionStatus(StrEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WCRStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class CommissioningStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMMISSIONED = "commissioned"
    FAILED = "failed"


# ── Meter ─────────────────────────────────────────────────────────────────────
class Meter(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "meter"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    meter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    meter_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # DISCOM assigned
    discom_asset_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    capacity_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    installed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "serial_number", name="uq_meter_serial"),
        Index("ix_meter_project", "organization_id", "project_id"),
    )


# ── Inspection Template ───────────────────────────────────────────────────────
class InspectionTemplate(Base, TenantMixin, TimestampMixin):
    __tablename__ = "inspection_template"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Each check item: {code, label, type: pass_fail|numeric|text, required: bool, hint: str}
    checklist: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_insp_template_code"),
    )


# ── Inspection ────────────────────────────────────────────────────────────────
class Inspection(Base, TenantMixin, TimestampMixin):
    __tablename__ = "inspection"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection_template.id", ondelete="SET NULL"), nullable=True
    )
    inspector_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    conducted_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=InspectionStatus.SCHEDULED)
    score_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    overall_result: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # pass/fail
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geo_location: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    items: Mapped[list[InspectionItem]] = relationship(
        "InspectionItem", back_populates="inspection", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_inspection_project", "organization_id", "project_id"),
        Index("ix_inspection_status", "organization_id", "status"),
    )


# ── Inspection Item ───────────────────────────────────────────────────────────
class InspectionItem(Base, TenantMixin, TimestampMixin):
    __tablename__ = "inspection_item"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inspection.id", ondelete="CASCADE"), nullable=False
    )
    check_code: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    result: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pass/fail/value
    numeric_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    text_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    inspection: Mapped[Inspection] = relationship("Inspection", back_populates="items")

    __table_args__ = (
        Index("ix_insp_item_inspection", "inspection_id"),
    )


# ── WCR (Work Completion Report) ──────────────────────────────────────────────
class WCR(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "wcr"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    wcr_number: Mapped[str] = mapped_column(String(100), nullable=False)
    wcr_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=WCRStatus.DRAFT)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    capacity_installed_kw: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # References to asset IDs installed
    asset_ids: Mapped[list[str]] = mapped_column(ARRAY(String(36)), nullable=False, default=list)
    # Content-addressed PDF
    document_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    submitted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "wcr_number", "wcr_version", name="uq_wcr_num_ver"),
        Index("ix_wcr_project", "organization_id", "project_id"),
    )


# ── Commissioning Record ──────────────────────────────────────────────────────
class CommissioningRecord(Base, TenantMixin, TimestampMixin):
    __tablename__ = "commissioning_record"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=CommissioningStatus.PENDING)
    commissioned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    commissioned_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    grid_synchronization_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    initial_generation_kwh: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    test_results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    checklist_results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    discom_approval_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "project_id", name="uq_commissioning_project"),
        Index("ix_commissioning_plant", "organization_id", "plant_id"),
    )
