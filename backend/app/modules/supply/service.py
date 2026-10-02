"""
Solar Operations OS — Supply Chain Service Interface
Manages Suppliers, Purchase Orders, Shipments, Warehouses, and Stock Movements.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.supply.events import POCreated, ShipmentReceived, StockAdjusted
from app.modules.supply.models import (
    POLine,
    POStatus,
    PurchaseOrder,
    Shipment,
    ShipmentLine,
    ShipmentStatus,
    StockMovement,
    StockMovementType,
    Supplier,
    Warehouse,
)
from app.modules.supply.public import (
    PurchaseOrderCreate,
    ShipmentCreate,
    SupplierCreate,
    WarehouseCreate,
)


class SupplyService:
    # ── Supplier ──────────────────────────────────────────────────────────────
    async def create_supplier(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: SupplierCreate,
    ) -> Supplier:
        existing = (await session.execute(
            select(Supplier).where(
                Supplier.organization_id == org_id,
                Supplier.code == data.code,
                Supplier.deleted_at.is_(None),
            )
        )).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Supplier with code '{data.code}' already exists")

        supplier = Supplier(organization_id=org_id, **data.model_dump())
        session.add(supplier)
        await session.flush()
        return supplier

    async def list_suppliers(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
    ) -> List[Supplier]:
        stmt = select(Supplier).where(
            Supplier.organization_id == org_id,
            Supplier.deleted_at.is_(None),
        ).order_by(Supplier.name)
        return list((await session.execute(stmt)).scalars().all())

    # ── Warehouse ─────────────────────────────────────────────────────────────
    async def create_warehouse(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: WarehouseCreate,
    ) -> Warehouse:
        existing = (await session.execute(
            select(Warehouse).where(
                Warehouse.organization_id == org_id,
                Warehouse.code == data.code,
            )
        )).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Warehouse with code '{data.code}' already exists")
        wh = Warehouse(organization_id=org_id, **data.model_dump())
        session.add(wh)
        await session.flush()
        return wh

    # ── Purchase Order ────────────────────────────────────────────────────────
    async def create_po(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: PurchaseOrderCreate,
        actor_id: uuid.UUID,
    ) -> PurchaseOrder:
        # Verify supplier
        supplier = (await session.execute(
            select(Supplier).where(
                Supplier.id == data.supplier_id,
                Supplier.organization_id == org_id,
                Supplier.deleted_at.is_(None),
            )
        )).scalar_one_or_none()
        if not supplier:
            raise NotFoundError("Supplier", str(data.supplier_id))

        # Check PO number uniqueness
        dup = (await session.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.organization_id == org_id,
                PurchaseOrder.po_number == data.po_number,
            )
        )).scalar_one_or_none()
        if dup:
            raise ConflictError(f"PO number '{data.po_number}' already exists")

        # Calculate totals
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        for line in data.lines:
            line_total = Decimal(str(line.unit_price)) * Decimal(str(line.ordered_quantity))
            tax = line_total * Decimal(str(line.tax_rate_percent)) / 100
            subtotal += line_total
            tax_total += tax

        po = PurchaseOrder(
            organization_id=org_id,
            po_number=data.po_number,
            supplier_id=data.supplier_id,
            project_id=data.project_id,
            status=POStatus.DRAFT,
            order_date=data.order_date or datetime.now(timezone.utc),
            expected_delivery_date=data.expected_delivery_date,
            currency=data.currency,
            subtotal_amount=float(subtotal),
            tax_amount=float(tax_total),
            total_amount=float(subtotal + tax_total),
        )
        session.add(po)
        await session.flush()

        for line_data in data.lines:
            line_total = (
                Decimal(str(line_data.unit_price)) * Decimal(str(line_data.ordered_quantity))
                * (1 + Decimal(str(line_data.tax_rate_percent)) / 100)
            )
            session.add(POLine(
                organization_id=org_id,
                purchase_order_id=po.id,
                bom_item_id=line_data.bom_item_id,
                item_description=line_data.item_description,
                ordered_quantity=line_data.ordered_quantity,
                unit_of_measure=line_data.unit_of_measure,
                unit_price=line_data.unit_price,
                tax_rate_percent=line_data.tax_rate_percent,
                total_amount=float(line_total),
            ))
        await session.flush()

        await event_bus.publish(POCreated(
            organization_id=org_id,
            po_id=po.id,
            po_number=data.po_number,
            supplier_id=data.supplier_id,
            total_amount=float(subtotal + tax_total),
        ))
        return po

    async def issue_po(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        po_id: uuid.UUID,
    ) -> PurchaseOrder:
        po = await self._get_po(session, org_id, po_id)
        if po.status != POStatus.DRAFT:
            raise ConflictError("Only DRAFT POs can be issued")
        po.status = POStatus.ISSUED
        session.add(po)
        return po

    async def get_po(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        po_id: uuid.UUID,
    ) -> PurchaseOrder:
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.organization_id == org_id,
        ).options(selectinload(PurchaseOrder.lines))
        po = (await session.execute(stmt)).scalar_one_or_none()
        if not po:
            raise NotFoundError("PurchaseOrder", str(po_id))
        return po

    # ── Shipment ──────────────────────────────────────────────────────────────
    async def create_shipment(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: ShipmentCreate,
        actor_id: uuid.UUID,
    ) -> Shipment:
        po = await self._get_po(session, org_id, data.purchase_order_id)
        if po.status not in (POStatus.ISSUED, POStatus.PARTIAL_RECEIVED):
            raise ValidationError("PO must be in ISSUED or PARTIAL_RECEIVED status to create shipment")

        shipment = Shipment(
            organization_id=org_id,
            purchase_order_id=data.purchase_order_id,
            destination_warehouse_id=data.destination_warehouse_id,
            tracking_number=data.tracking_number,
            transporter_name=data.transporter_name,
            lr_number=data.lr_number,
            status=ShipmentStatus.DISPATCHED,
            dispatch_date=data.dispatch_date,
        )
        session.add(shipment)
        await session.flush()

        for line_data in data.lines:
            session.add(ShipmentLine(
                organization_id=org_id,
                shipment_id=shipment.id,
                po_line_id=line_data.po_line_id,
                dispatched_quantity=line_data.dispatched_quantity,
                notes=line_data.notes,
            ))
        await session.flush()
        return shipment

    async def mark_delivered(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        shipment_id: uuid.UUID,
    ) -> Shipment:
        shipment = await self._get_shipment(session, org_id, shipment_id)
        if shipment.status == ShipmentStatus.DELIVERED:
            raise ConflictError("Shipment already delivered")
        shipment.status = ShipmentStatus.DELIVERED
        shipment.delivered_date = datetime.now(timezone.utc)
        session.add(shipment)

        # Update PO status
        po = await self._get_po(session, org_id, shipment.purchase_order_id)
        po.status = POStatus.PARTIAL_RECEIVED
        session.add(po)

        await event_bus.publish(ShipmentReceived(
            organization_id=org_id,
            shipment_id=shipment_id,
            po_id=shipment.purchase_order_id,
            warehouse_id=shipment.destination_warehouse_id,
        ))
        return shipment

    # ── Internals ─────────────────────────────────────────────────────────────
    async def _get_po(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        po_id: uuid.UUID,
    ) -> PurchaseOrder:
        po = (await session.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.id == po_id,
                PurchaseOrder.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if not po:
            raise NotFoundError("PurchaseOrder", str(po_id))
        return po

    async def _get_shipment(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        shipment_id: uuid.UUID,
    ) -> Shipment:
        s = (await session.execute(
            select(Shipment).where(
                Shipment.id == shipment_id,
                Shipment.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if not s:
            raise NotFoundError("Shipment", str(shipment_id))
        return s


supply_service = SupplyService()
