"""
Solar Operations OS — Warranty Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.warranty.public import (
    WarrantyClaimCreate,
    WarrantyClaimOut,
    WarrantyClaimStatusUpdate,
    WarrantyCreate,
    WarrantyOut,
)
from app.modules.warranty.service import warranty_service

router = APIRouter(prefix="/warranty", tags=["Warranty"])


# ── Warranty ──────────────────────────────────────────────────────────────────
@router.post(
    "/warranties",
    response_model=WarrantyOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_warranty(
    payload: WarrantyCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_MANAGE)),
) -> WarrantyOut:
    warranty = await warranty_service.register_warranty(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(warranty)
    return WarrantyOut.model_validate(warranty)


@router.get("/warranties/{warranty_id}", response_model=WarrantyOut)
async def get_warranty(
    warranty_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_READ)),
) -> WarrantyOut:
    item = await warranty_service.get_warranty(session, current_user.org_id, warranty_id)
    return WarrantyOut.model_validate(item)


@router.get("/projects/{project_id}/warranties", response_model=List[WarrantyOut])
async def list_warranties_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_READ)),
) -> List[WarrantyOut]:
    items = await warranty_service.list_warranties_for_project(
        session, current_user.org_id, project_id
    )
    return [WarrantyOut.model_validate(i) for i in items]


# ── Claims ────────────────────────────────────────────────────────────────────
@router.post(
    "/claims",
    response_model=WarrantyClaimOut,
    status_code=status.HTTP_201_CREATED,
)
async def open_claim(
    payload: WarrantyClaimCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_CLAIM)),
) -> WarrantyClaimOut:
    claim = await warranty_service.open_claim(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    full_claim = await warranty_service.get_claim(session, current_user.org_id, claim.id)
    return WarrantyClaimOut.model_validate(full_claim)


@router.post("/claims/{claim_id}/status", response_model=WarrantyClaimOut)
async def update_claim_status(
    claim_id: uuid.UUID,
    payload: WarrantyClaimStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_CLAIM)),
) -> WarrantyClaimOut:
    claim = await warranty_service.update_claim_status(
        session, current_user.org_id, claim_id, payload, actor_id=current_user.id
    )
    await session.commit()
    full_claim = await warranty_service.get_claim(session, current_user.org_id, claim.id)
    return WarrantyClaimOut.model_validate(full_claim)


@router.get("/claims/{claim_id}", response_model=WarrantyClaimOut)
async def get_claim(
    claim_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_READ)),
) -> WarrantyClaimOut:
    claim = await warranty_service.get_claim(session, current_user.org_id, claim_id)
    return WarrantyClaimOut.model_validate(claim)


@router.get("/warranties/{warranty_id}/claims", response_model=List[WarrantyClaimOut])
async def list_claims_for_warranty(
    warranty_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.WARRANTY_READ)),
) -> List[WarrantyClaimOut]:
    items = await warranty_service.list_claims_for_warranty(
        session, current_user.org_id, warranty_id
    )
    return [WarrantyClaimOut.model_validate(i) for i in items]
