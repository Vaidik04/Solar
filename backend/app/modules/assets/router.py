"""
Solar Operations OS — Asset Registry Module: API Router
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.assets.public import (
    AssetAllocate,
    AssetInstall,
    AssetRead,
    AssetRegister,
    AssetTypeCreate,
    AssetTypeRead,
)
from app.modules.assets.service import asset_service

router = APIRouter(prefix="/assets", tags=["Asset Registry & Traceability"])


@router.post(
    "/types",
    response_model=AssetTypeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ASSETS_REGISTER))],
)
async def create_asset_type(
    data: AssetTypeCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetTypeRead:
    asset_type = await asset_service.create_asset_type(session, user.org_id, data)
    await session.commit()
    return AssetTypeRead.model_validate(asset_type)


@router.post(
    "",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ASSETS_REGISTER))],
)
async def register_asset(
    data: AssetRegister,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetRead:
    asset = await asset_service.register_asset(session, user.org_id, user.user_id, data)
    await session.commit()
    return AssetRead.model_validate(asset)


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    dependencies=[Depends(require_permission(Permission.ASSETS_READ))],
)
async def get_asset(
    asset_id: uuid.UUID,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetRead:
    asset = await asset_service.get_asset(session, user.org_id, asset_id)
    return AssetRead.model_validate(asset)


@router.post(
    "/{asset_id}/allocate",
    response_model=AssetRead,
    dependencies=[Depends(require_permission(Permission.ASSETS_ALLOCATE))],
)
async def allocate_asset(
    asset_id: uuid.UUID,
    data: AssetAllocate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetRead:
    asset = await asset_service.allocate_asset(session, user.org_id, asset_id, user.user_id, data)
    await session.commit()
    return AssetRead.model_validate(asset)


@router.post(
    "/{asset_id}/install",
    response_model=AssetRead,
    dependencies=[Depends(require_permission(Permission.ASSETS_EVENT_RECORD))],
)
async def install_asset(
    asset_id: uuid.UUID,
    data: AssetInstall,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetRead:
    asset = await asset_service.install_asset(session, user.org_id, asset_id, user.user_id, data)
    await session.commit()
    return AssetRead.model_validate(asset)


@router.get(
    "/qr/{qr_token}",
    response_model=AssetRead,
    dependencies=[Depends(require_permission(Permission.ASSETS_READ))],
)
async def scan_qr_token(
    qr_token: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AssetRead:
    asset = await asset_service.get_by_qr_token(session, qr_token)
    return AssetRead.model_validate(asset)
