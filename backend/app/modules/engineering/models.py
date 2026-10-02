"""
Solar Operations OS — Engineering & Design Module: Database Models
Owns: Design, BOM, BOMItem, StringConfiguration, ExpectedGeneration
"""
from __future__ import annotations

import uuid
from datetime import datetime
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


class SystemType(StrEnum):
    GRID_TIED = "grid_tied"
    HYBRID = "hybrid"
    OFF_GRID = "off_grid"
    BESS_COUPLED = "bess_coupled"


class DesignStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    SUPERSEDED = "superseded"


class BOMStatus(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    LOCKED = "locked"


class BOMCategory(StrEnum):
    SOLAR_MODULE = "solar_module"
    INVERTER = "inverter"
    MOUNTING_STRUCTURE = "mounting_structure"
    SOLAR_CABLE_DC = "solar_cable_dc"
    POWER_CABLE_AC = "power_cable_ac"
    ACDB = "acdb"
    DCDB = "dcdb"
    EARTHING_KIT = "earthing_kit"
    LIGHTNING_ARRESTER = "lightning_arrester"
    NET_METER = "net_meter"
    GENSET_CONTROLLER = "genset_controller"
    OTHER = "other"


# ── Design ────────────────────────────────────────────────────────────────────
class Design(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "design"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    design_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Preliminary Design")
    system_type: Mapped[str] = mapped_column(String(50), nullable=False, default=SystemType.GRID_TIED)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DesignStatus.DRAFT)

    # Technical Specs
    capacity_kw_dc: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity_kw_ac: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    panel_make: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_model: Mapped[str] = mapped_column(String(100), nullable=False)
    panel_wattage: Mapped[float] = mapped_column(Numeric(6, 1), nullable=False)  # e.g., 550.0 Wp
    panel_count: Mapped[int] = mapped_column(Integer, nullable=False)
    inverter_make: Mapped[str] = mapped_column(String(100), nullable=False)
    inverter_model: Mapped[str] = mapped_column(String(100), nullable=False)
    inverter_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Orientation & Layout
    tilt_degrees: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=15.0)
    azimuth_degrees: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=180.0)
    expected_annual_generation_kwh: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    performance_ratio_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True, default=78.5)

    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    boms: Mapped[list[BOM]] = relationship("BOM", back_populates="design", cascade="all, delete-orphan")
    string_configurations: Mapped[list[StringConfiguration]] = relationship(
        "StringConfiguration", back_populates="design", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "project_id", "design_version", name="uq_design_project_ver"),
        Index("ix_design_project", "project_id"),
    )


# ── String Configuration ──────────────────────────────────────────────────────
class StringConfiguration(Base, TenantMixin, TimestampMixin):
    __tablename__ = "string_configuration"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design.id", ondelete="CASCADE"), nullable=False
    )
    string_number: Mapped[int] = mapped_column(Integer, nullable=False)
    inverter_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    mppt_tracker_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    panels_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Electrical parameters at STC
    vmp_volts: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    voc_volts: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    imp_amps: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    isc_amps: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    design: Mapped[Design] = relationship("Design", back_populates="string_configurations")

    __table_args__ = (
        UniqueConstraint("design_id", "string_number", name="uq_string_config_num"),
    )


# ── Bill of Materials (BOM) ───────────────────────────────────────────────────
class BOM(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "bom"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design.id", ondelete="CASCADE"), nullable=False
    )
    bom_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=BOMStatus.DRAFT)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )

    items: Mapped[list[BOMItem]] = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")
    design: Mapped[Design] = relationship("Design", back_populates="boms")

    __table_args__ = (
        UniqueConstraint("organization_id", "project_id", "bom_version", name="uq_bom_project_ver"),
    )


# ── BOM Item ──────────────────────────────────────────────────────────────────
class BOMItem(Base, TenantMixin, TimestampMixin):
    __tablename__ = "bom_item"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bom.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="NOS")  # NOS, MTR, SET, LOT
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    bom: Mapped[BOM] = relationship("BOM", back_populates="items")

    __table_args__ = (
        Index("ix_bom_item_bom", "bom_id"),
        Index("ix_bom_item_category", "bom_id", "category"),
    )
