"""
Solar Operations OS — CRM & Sites Module: API Router
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.crm.models import PhotoCategory
from app.modules.crm.public import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    SiteCreate,
    SitePhotoRead,
    SiteRead,
    SiteSurveyCreate,
    SiteSurveyRead,
    SiteUpdate,
)
from app.modules.crm.service import crm_service

router = APIRouter(prefix="/crm", tags=["CRM & Sites"])


# ── Customer Endpoints ────────────────────────────────────────────────────────
@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CRM_CUSTOMER_CREATE))],
)
async def create_customer(
    data: CustomerCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerRead:
    customer = await crm_service.create_customer(session, user.org_id, data)
    await session.commit()
    return CustomerRead.model_validate(customer)


@router.get(
    "/customers",
    response_model=List[CustomerRead],
    dependencies=[Depends(require_permission(Permission.CRM_CUSTOMER_READ))],
)
async def list_customers(
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    query: Optional[str] = Query(None, min_length=2),
) -> List[CustomerRead]:
    customers, _ = await crm_service.list_customers(
        session, user.org_id, limit=limit, offset=offset, query=query
    )
    return [CustomerRead.model_validate(c) for c in customers]


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(require_permission(Permission.CRM_CUSTOMER_READ))],
)
async def get_customer(
    customer_id: uuid.UUID,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerRead:
    customer = await crm_service.get_customer(session, user.org_id, customer_id)
    return CustomerRead.model_validate(customer)


@router.patch(
    "/customers/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(require_permission(Permission.CRM_CUSTOMER_UPDATE))],
)
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerRead:
    customer = await crm_service.update_customer(session, user.org_id, customer_id, data)
    await session.commit()
    return CustomerRead.model_validate(customer)


# ── Site Endpoints ────────────────────────────────────────────────────────────
@router.post(
    "/sites",
    response_model=SiteRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CRM_SITE_CREATE))],
)
async def create_site(
    data: SiteCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SiteRead:
    site = await crm_service.create_site(session, user.org_id, data)
    await session.commit()
    return SiteRead.model_validate(site)


@router.get(
    "/sites",
    response_model=List[SiteRead],
    dependencies=[Depends(require_permission(Permission.CRM_SITE_READ))],
)
async def list_sites(
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    customer_id: Optional[uuid.UUID] = Query(None),
    branch_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[SiteRead]:
    sites, _ = await crm_service.list_sites(
        session, user.org_id, customer_id=customer_id, branch_id=branch_id, limit=limit, offset=offset
    )
    return [SiteRead.model_validate(s) for s in sites]


@router.get(
    "/sites/{site_id}",
    response_model=SiteRead,
    dependencies=[Depends(require_permission(Permission.CRM_SITE_READ))],
)
async def get_site(
    site_id: uuid.UUID,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SiteRead:
    site = await crm_service.get_site(session, user.org_id, site_id)
    return SiteRead.model_validate(site)


# ── Site Survey Endpoints ─────────────────────────────────────────────────────
@router.post(
    "/sites/{site_id}/surveys",
    response_model=SiteSurveyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CRM_SITE_UPDATE))],
)
async def create_site_survey(
    site_id: uuid.UUID,
    data: SiteSurveyCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SiteSurveyRead:
    survey = await crm_service.create_survey(session, user.org_id, site_id, data)
    await session.commit()
    return SiteSurveyRead.model_validate(survey)


# ── Site Photo Upload Endpoint ────────────────────────────────────────────────
@router.post(
    "/sites/{site_id}/photos",
    response_model=SitePhotoRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CRM_SITE_UPDATE))],
)
async def upload_site_photo(
    site_id: uuid.UUID,
    file: UploadFile = File(...),
    category: PhotoCategory = Form(PhotoCategory.ROOF),
    caption: Optional[str] = Form(None),
    survey_id: Optional[uuid.UUID] = Form(None),
    exif_lat: Optional[float] = Form(None),
    exif_lon: Optional[float] = Form(None),
    user: Annotated[UserContext, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> SitePhotoRead:
    content = await file.read()
    photo = await crm_service.upload_site_photo(
        session=session,
        org_id=user.org_id,
        site_id=site_id,
        uploader_user_id=user.user_id,
        photo_bytes=content,
        filename=file.filename or "photo.jpg",
        category=category,
        mime_type=file.content_type or "image/jpeg",
        survey_id=survey_id,
        caption=caption,
        exif_lat=exif_lat,
        exif_lon=exif_lon,
    )
    await session.commit()
    return SitePhotoRead.model_validate(photo)
