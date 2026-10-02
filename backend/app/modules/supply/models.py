"""
Solar Operations OS — Supply Chain & Procurement: Database Models
Owns: Supplier, PurchaseOrder, POLine, Shipment, ShipmentLine, Warehouse, StockMovement
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


class POStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIAL_RECEIVED = "partial_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ShipmentStatus(StrEnum):
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DAMAGED = "damaged"


class StockMovementType(StrEnum):
    INWARD_FROM_PO = "inward_from_po"
    TRANSFER_BETWEEN_WAREHOUSES = "transfer_between_warehouses"
    DISPATCH_TO_SITE = "dispatch_to_site"
    RETURN_FROM_SITE = "return_from_site"
    SCRAP_OR_DAMAGE = "scrap_or_damage"


# ── Supplier ──────────────────────────────────────────────────────────────────
class Supplier(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "supplier"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)

    purchase_orders: Mapped[list[PurchaseOrder]] = relationship("PurchaseOrder", back_populates="supplier")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_supplier_org_code"),
        Index("ix_supplier_name", "organization_id", "name"),
    )


# ── Warehouse ─────────────────────────────────────────────────────────────────
class Warehouse(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "warehouse"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouse_org_code"),
    )


# ── Purchase Order ────────────────────────────────────────────────────────────
class PurchaseOrder(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "purchase_order"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("supplier.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=POStatus.DRAFT)
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    subtotal_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)

    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="purchase_orders")
    lines: Mapped[list[POLine]] = relationship("POLine", back_populates="purchase_order", cascade="all, delete-orphan")
    shipments: Mapped[list[Shipment]] = relationship("Shipment", back_populates="purchase_order")

    __table_args__ = (
        UniqueConstraint("organization_id", "po_number", name="uq_po_org_num"),
        Index("ix_po_supplier", "organization_id", "supplier_id"),
        Index("ix_po_project", "organization_id", "project_id"),
    )


# ── Purchase Order Line ───────────────────────────────────────────────────────
class POLine(Base, TenantMixin, TimestampMixin):
    __tablename__ = "po_line"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False
    )
    bom_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bom_item.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    ordered_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    received_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="NOS")
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=18.0)  # GST 18%
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (
        Index("ix_po_line_po", "purchase_order_id"),
    )


# ── Shipment ──────────────────────────────────────────────────────────────────
class Shipment(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "shipment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False
    )
    destination_warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transporter_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lr_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Lorry Receipt No.
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ShipmentStatus.DISPATCHED)
    dispatch_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="shipments")
    lines: Mapped[list[ShipmentLine]] = relationship("ShipmentLine", back_populates="shipment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_shipment_po", "purchase_order_id"),
        Index("ix_shipment_status", "organization_id", "status"),
    )


# ── Shipment Line ─────────────────────────────────────────────────────────────
class ShipmentLine(Base, TenantMixin, TimestampMixin):
    __tablename__ = "shipment_line"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shipment.id", ondelete="CASCADE"), nullable=False
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("po_line.id", ondelete="CASCADE"), nullable=False
    )
    dispatched_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    accepted_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    rejected_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    shipment: Mapped[Shipment] = relationship("Shipment", back_populates="lines")

    __table_args__ = (
        Index("ix_shipment_line_shipment", "shipment_id"),
    )


# ── Stock Movement ────────────────────────────────────────────────────────────
class StockMovement(Base, TenantMixin, TimestampMixin):
    __tablename__ = "stock_movement"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="SET NULL"), nullable=True
    )
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True
    )
    to_warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouse.id", ondelete="SET NULL"), nullable=True
    )
    to_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=1.0)
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_stock_movement_asset", "asset_id"),
        Index("ix_stock_movement_to_proj", "to_project_id"),
    )
