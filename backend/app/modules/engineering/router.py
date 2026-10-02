"""
Solar Operations OS — Engineering Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.modules.engineering.public import BOMCreate, BOMOut, BOMItemOut, DesignCreate, DesignOut, DesignUpdate
from app.modules.engineering.service import engineering_service
from app.modules.identity.models import User

router = APIRouter(prefix="/engineering", tags=["Engineering"])


@router.post("/designs", response_model=DesignOut, status_code=status.HTTP_201_CREATED)
async def create_design(
    payload: DesignCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:design:create")),
) -> DesignOut:
    design = await engineering_service.create_design(
        session, current_user.organization_id, payload, current_user.id
    )
    await session.commit()
    await session.refresh(design)
    return DesignOut.model_validate(design)


@router.get("/designs", response_model=List[DesignOut])
async def list_designs(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:design:read")),
) -> List[DesignOut]:
    designs = await engineering_service.list_designs(session, current_user.organization_id, project_id)
    return [DesignOut.model_validate(d) for d in designs]


@router.get("/designs/{design_id}", response_model=DesignOut)
async def get_design(
    design_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:design:read")),
) -> DesignOut:
    design = await engineering_service.get_design(session, current_user.organization_id, design_id)
    return DesignOut.model_validate(design)


@router.post("/designs/{design_id}/approve", response_model=DesignOut)
async def approve_design(
    design_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:design:approve")),
) -> DesignOut:
    design = await engineering_service.approve_design(
        session, current_user.organization_id, design_id, current_user.id
    )
    await session.commit()
    await session.refresh(design)
    return DesignOut.model_validate(design)


@router.post("/boms", response_model=BOMOut, status_code=status.HTTP_201_CREATED)
async def create_bom(
    payload: BOMCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:bom:create")),
) -> BOMOut:
    bom = await engineering_service.create_bom(
        session, current_user.organization_id, payload, current_user.id
    )
    await session.commit()
    await session.refresh(bom)
    return BOMOut.model_validate(bom)


@router.post("/boms/{bom_id}/finalize", response_model=BOMOut)
async def finalize_bom(
    bom_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:bom:finalize")),
) -> BOMOut:
    bom = await engineering_service.finalize_bom(
        session, current_user.organization_id, bom_id, current_user.id
    )
    await session.commit()
    await session.refresh(bom)
    return BOMOut.model_validate(bom)


@router.get("/boms/{bom_id}", response_model=BOMOut)
async def get_bom(
    bom_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_permission("engineering:bom:read")),
) -> BOMOut:
    bom = await engineering_service.get_bom(session, current_user.organization_id, bom_id)
    return BOMOut.model_validate(bom)
