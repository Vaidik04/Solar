"""
Solar Operations OS — Field Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.field.public import (
    CommissioningCreate,
    CommissioningOut,
    InspectionCreate,
    InspectionOut,
    InspectionSubmit,
    InspectionTemplateCreate,
    InspectionTemplateOut,
    MeterCreate,
    MeterOut,
    WCRCreate,
    WCROut,
)
from app.modules.field.service import field_service

router = APIRouter(prefix="/field", tags=["Field"])


# ── Meters ────────────────────────────────────────────────────────────────────
@router.post(
    "/meters",
    response_model=MeterOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_meter(
    payload: MeterCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_METER_MANAGE)),
) -> MeterOut:
    meter = await field_service.register_meter(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(meter)
    return MeterOut.model_validate(meter)


@router.get("/projects/{project_id}/meters", response_model=List[MeterOut])
async def list_meters_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_METER_MANAGE)),
) -> List[MeterOut]:
    items = await field_service.list_meters_for_project(session, current_user.org_id, project_id)
    return [MeterOut.model_validate(i) for i in items]


@router.get("/meters/{meter_id}", response_model=MeterOut)
async def get_meter(
    meter_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_METER_MANAGE)),
) -> MeterOut:
    item = await field_service.get_meter(session, current_user.org_id, meter_id)
    return MeterOut.model_validate(item)


# ── Inspection Templates ──────────────────────────────────────────────────────
@router.post(
    "/templates",
    response_model=InspectionTemplateOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_inspection_template(
    payload: InspectionTemplateCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> InspectionTemplateOut:
    tmpl = await field_service.create_template(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(tmpl)
    return InspectionTemplateOut.model_validate(tmpl)


@router.get("/templates", response_model=List[InspectionTemplateOut])
async def list_inspection_templates(
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> List[InspectionTemplateOut]:
    items = await field_service.list_templates(session, current_user.org_id)
    return [InspectionTemplateOut.model_validate(i) for i in items]


# ── Inspections ───────────────────────────────────────────────────────────────
@router.post(
    "/inspections",
    response_model=InspectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_inspection(
    payload: InspectionCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> InspectionOut:
    insp = await field_service.create_inspection(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(insp)
    return InspectionOut.model_validate(insp)


@router.post(
    "/inspections/{inspection_id}/submit",
    response_model=InspectionOut,
)
async def submit_inspection(
    inspection_id: uuid.UUID,
    payload: InspectionSubmit,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> InspectionOut:
    insp = await field_service.submit_inspection(
        session, current_user.org_id, inspection_id, payload
    )
    await session.commit()
    full_insp = await field_service.get_inspection(session, current_user.org_id, insp.id)
    return InspectionOut.model_validate(full_insp)


@router.get("/inspections/{inspection_id}", response_model=InspectionOut)
async def get_inspection(
    inspection_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> InspectionOut:
    insp = await field_service.get_inspection(session, current_user.org_id, inspection_id)
    return InspectionOut.model_validate(insp)


@router.get("/projects/{project_id}/inspections", response_model=List[InspectionOut])
async def list_inspections_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_INSPECTION_MANAGE)),
) -> List[InspectionOut]:
    items = await field_service.list_inspections_for_project(
        session, current_user.org_id, project_id
    )
    return [InspectionOut.model_validate(i) for i in items]


# ── WCR ───────────────────────────────────────────────────────────────────────
@router.post(
    "/wcrs",
    response_model=WCROut,
    status_code=status.HTTP_201_CREATED,
)
async def create_wcr(
    payload: WCRCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_WCR_GENERATE)),
) -> WCROut:
    wcr = await field_service.create_wcr(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    await session.refresh(wcr)
    return WCROut.model_validate(wcr)


@router.get("/wcrs/{wcr_id}", response_model=WCROut)
async def get_wcr(
    wcr_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_WCR_GENERATE)),
) -> WCROut:
    item = await field_service.get_wcr(session, current_user.org_id, wcr_id)
    return WCROut.model_validate(item)


@router.get("/projects/{project_id}/wcrs", response_model=List[WCROut])
async def list_wcrs_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_WCR_GENERATE)),
) -> List[WCROut]:
    items = await field_service.list_wcrs_for_project(session, current_user.org_id, project_id)
    return [WCROut.model_validate(i) for i in items]


# ── Commissioning ─────────────────────────────────────────────────────────────
@router.post(
    "/commissioning",
    response_model=CommissioningOut,
    status_code=status.HTTP_201_CREATED,
)
async def record_commissioning(
    payload: CommissioningCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_COMMISSION)),
) -> CommissioningOut:
    rec = await field_service.record_commissioning(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    await session.refresh(rec)
    return CommissioningOut.model_validate(rec)


@router.get("/projects/{project_id}/commissioning", response_model=CommissioningOut)
async def get_commissioning_record(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.FIELD_COMMISSION)),
) -> CommissioningOut:
    rec = await field_service.get_commissioning_record(
        session, current_user.org_id, project_id
    )
    return CommissioningOut.model_validate(rec)
