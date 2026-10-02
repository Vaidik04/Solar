"""
Solar Operations OS — Warranty Module: Database Models
Owns: Warranty, WarrantyClaim, ClaimEvent
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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin


class WarrantyType(StrEnum):
    MODULE_PERFORMANCE = "module_performance"
    MODULE_PRODUCT = "module_product"
    INVERTER_PRODUCT = "inverter_product"
    INVERTER_WORKMANSHIP = "inverter_workmanship"
    STRUCTURE = "structure"
    WORKMANSHIP = "workmanship"
    COMPREHENSIVE = "comprehensive"


class ClaimStatus(StrEnum):
    OPENED = "opened"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    RESOLVED_ACCEPTED = "resolved_accepted"
    RESOLVED_REJECTED = "resolved_rejected"
    WITHDRAWN = "withdrawn"


# ── Warranty ──────────────────────────────────────────────────────────────────
class Warranty(Base, TenantMixin, TimestampMixin):
    __tablename__ = "warranty"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="SET NULL"), nullable=True
    )
    warranty_type: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Manufacturer/Integrator
    certificate_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_years: Mapped[int] = mapped_column(Integer, nullable=False)
    coverage_details: Mapped[str] = mapped_column(Text, nullable=False)
    exclusions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    claims: Mapped[list[WarrantyClaim]] = relationship(
        "WarrantyClaim", back_populates="warranty", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_warranty_project", "organization_id", "project_id"),
        Index("ix_warranty_plant", "organization_id", "plant_id"),
        Index("ix_warranty_end", "organization_id", "end_date"),
    )


# ── Warranty Claim ────────────────────────────────────────────────────────────
class WarrantyClaim(Base, TenantMixin, TimestampMixin):
    __tablename__ = "warranty_claim"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warranty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warranty.id", ondelete="CASCADE"), nullable=False
    )
    claim_number: Mapped[str] = mapped_column(String(100), nullable=False)
    opened_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ClaimStatus.OPENED)
    defect_description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_components: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, default=list)
    reported_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replacement_asset_ids: Mapped[list[str]] = mapped_column(ARRAY(String(36)), nullable=False, default=list)

    warranty: Mapped[Warranty] = relationship("Warranty", back_populates="claims")
    events: Mapped[list[ClaimEvent]] = relationship(
        "ClaimEvent", back_populates="claim", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "claim_number", name="uq_claim_number"),
        Index("ix_claim_warranty", "warranty_id"),
    )


# ── Claim Event (timeline) ────────────────────────────────────────────────────
class ClaimEvent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "claim_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warranty_claim.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    event_meta: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    claim: Mapped[WarrantyClaim] = relationship("WarrantyClaim", back_populates="events")

    __table_args__ = (
        Index("ix_claim_event_claim", "claim_id"),
    )
