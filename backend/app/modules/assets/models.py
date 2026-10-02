"""
Solar Operations OS — Asset Registry & Traceability: Database Models
Owns: AssetType, Asset, AssetEvent, AssetRelationship, QRToken
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


class AssetCategory(StrEnum):
    SOLAR_PANEL = "solar_panel"
    INVERTER = "inverter"
    ENERGY_METER = "energy_meter"
    TRANSFORMER = "transformer"
    DCDB = "dcdb"
    ACDB = "acdb"
    WEATHER_STATION = "weather_station"
    BATTERY_MODULE = "battery_module"
    STRUCTURE_TABLE = "structure_table"
    OTHER = "other"


class AssetStatus(StrEnum):
    IN_STOCK = "in_stock"
    ALLOCATED = "allocated"
    INSTALLED = "installed"
    COMMISSIONED = "commissioned"
    MAINTENANCE = "maintenance"
    RMA_REPLACED = "rma_replaced"
    RETIRED = "retired"


class AssetEventType(StrEnum):
    REGISTERED = "registered"
    ALLOCATED = "allocated"
    INSTALLED = "installed"
    COMMISSIONED = "commissioned"
    INSPECTED = "inspected"
    MAINTENANCE_PERFORMED = "maintenance_performed"
    WARRANTY_CLAIM_OPENED = "warranty_claim_opened"
    REPLACED = "replaced"
    RETIRED = "retired"


class RelationshipType(StrEnum):
    INVERTER_TO_STRING = "inverter_to_string"
    STRING_TO_PANEL = "string_to_panel"
    PANEL_TO_STRUCTURE = "panel_to_structure"
    METER_TO_INVERTER = "meter_to_inverter"


# ── Asset Type ────────────────────────────────────────────────────────────────
class AssetType(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "asset_type"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    nominal_rating_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    warranty_months: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # 5 years default
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    assets: Mapped[list[Asset]] = relationship("Asset", back_populates="asset_type")

    __table_args__ = (
        UniqueConstraint("organization_id", "category", "make", "model", name="uq_asset_type_make_model"),
        Index("ix_asset_type_category", "organization_id", "category"),
    )


# ── Asset ─────────────────────────────────────────────────────────────────────
class Asset(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    """
    Serial/QR tracked physical asset anchored to the Digital Plant Passport.
    Traceable over entire 25-year lifecycle.
    """
    __tablename__ = "asset"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset_type.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="SET NULL"), nullable=True
    )
    plant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Passport ID link

    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_serial: Mapped[str] = mapped_column(String(100), nullable=False)
    qr_token: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=AssetStatus.IN_STOCK)

    location_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # e.g., "Roof-North-String-04-Panel-12"
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    commissioned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    asset_type: Mapped[AssetType] = relationship("AssetType", back_populates="assets")
    events: Mapped[list[AssetEvent]] = relationship("AssetEvent", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_serial", name="uq_asset_org_normalized_serial"),
        Index("ix_asset_project", "organization_id", "project_id"),
        Index("ix_asset_plant", "organization_id", "plant_id"),
        Index("ix_asset_status", "organization_id", "status"),
    )


# ── Asset Event (Lifecycle History) ───────────────────────────────────────────
class AssetEvent(Base, TenantMixin, TimestampMixin):
    __tablename__ = "asset_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    asset: Mapped[Asset] = relationship("Asset", back_populates="events")

    __table_args__ = (
        Index("ix_asset_event_asset", "asset_id"),
        Index("ix_asset_event_org_type", "organization_id", "event_type"),
    )


# ── Asset Relationship (Hierarchy / Topology) ─────────────────────────────────
class AssetRelationship(Base, TenantMixin, TimestampMixin):
    __tablename__ = "asset_relationship"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    child_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("parent_asset_id", "child_asset_id", name="uq_asset_parent_child"),
    )
