"""
Solar Operations OS — Supply Chain Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.modules.supply.public import (
    PurchaseOrderCreate,
    PurchaseOrderOut,
    ShipmentCreate,
    ShipmentOut,
    SupplierCreate,
    SupplierOut,
    WarehouseCreate,
    WarehouseOut,
)
from app.modules.supply.service import supply_service
from app.modules.identity.models import User

router = APIRouter(prefix="/supply", tags=["Supply Chain"])


# ── Suppliers ─────────────────────────────────────────────────────────────────
@router.post("/suppliers", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:supplier:create")),
) -> SupplierOut:
    supplier = await supply_service.create_supplier(session, current_user.organization_id, payload)
    await session.commit()
    await session.refresh(supplier)
    return SupplierOut.model_validate(supplier)


@router.get("/suppliers", response_model=List[SupplierOut])
async def list_suppliers(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:supplier:read")),
) -> List[SupplierOut]:
    suppliers = await supply_service.list_suppliers(session, current_user.organization_id)
    return [SupplierOut.model_validate(s) for s in suppliers]


# ── Warehouses ────────────────────────────────────────────────────────────────
@router.post("/warehouses", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehouseCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:warehouse:create")),
) -> WarehouseOut:
    wh = await supply_service.create_warehouse(session, current_user.organization_id, payload)
    await session.commit()
    await session.refresh(wh)
    return WarehouseOut.model_validate(wh)


# ── Purchase Orders ───────────────────────────────────────────────────────────
@router.post("/purchase-orders", response_model=PurchaseOrderOut, status_code=status.HTTP_201_CREATED)
async def create_po(
    payload: PurchaseOrderCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:po:create")),
) -> PurchaseOrderOut:
    po = await supply_service.create_po(
        session, current_user.organization_id, payload, current_user.id
    )
    await session.commit()
    await session.refresh(po)
    return PurchaseOrderOut.model_validate(po)


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def get_po(
    po_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:po:read")),
) -> PurchaseOrderOut:
    po = await supply_service.get_po(session, current_user.organization_id, po_id)
    return PurchaseOrderOut.model_validate(po)


@router.post("/purchase-orders/{po_id}/issue", response_model=PurchaseOrderOut)
async def issue_po(
    po_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:po:issue")),
) -> PurchaseOrderOut:
    po = await supply_service.issue_po(session, current_user.organization_id, po_id)
    await session.commit()
    await session.refresh(po)
    return PurchaseOrderOut.model_validate(po)


# ── Shipments ─────────────────────────────────────────────────────────────────
@router.post("/shipments", response_model=ShipmentOut, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    payload: ShipmentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:shipment:create")),
) -> ShipmentOut:
    shipment = await supply_service.create_shipment(
        session, current_user.organization_id, payload, current_user.id
    )
    await session.commit()
    await session.refresh(shipment)
    return ShipmentOut.model_validate(shipment)


@router.post("/shipments/{shipment_id}/deliver", response_model=ShipmentOut)
async def mark_delivered(
    shipment_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("supply:shipment:update")),
) -> ShipmentOut:
    shipment = await supply_service.mark_delivered(
        session, current_user.organization_id, shipment_id
    )
    await session.commit()
    await session.refresh(shipment)
    return ShipmentOut.model_validate(shipment)
