"""
Solar Operations OS — Compliance Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.compliance.public import (
    ComplianceRunOut,
    ComplianceRunTrigger,
    ComplianceWaiverCreate,
    ComplianceWaiverOut,
)
from app.modules.compliance.service import compliance_service

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post(
    "/runs",
    response_model=ComplianceRunOut,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_compliance_run(
    payload: ComplianceRunTrigger,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_RUN)),
) -> ComplianceRunOut:
    run = await compliance_service.run_compliance(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    # Reload with results
    full_run = await compliance_service.get_run(session, current_user.org_id, run.id)
    return ComplianceRunOut.model_validate(full_run)


@router.get("/runs/{run_id}", response_model=ComplianceRunOut)
async def get_compliance_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_READ)),
) -> ComplianceRunOut:
    run = await compliance_service.get_run(session, current_user.org_id, run_id)
    return ComplianceRunOut.model_validate(run)


@router.get("/projects/{project_id}/runs", response_model=List[ComplianceRunOut])
async def list_runs_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_READ)),
) -> List[ComplianceRunOut]:
    runs = await compliance_service.list_runs_for_project(
        session, current_user.org_id, project_id
    )
    return [ComplianceRunOut.model_validate(r) for r in runs]


@router.post(
    "/waivers",
    response_model=ComplianceWaiverOut,
    status_code=status.HTTP_201_CREATED,
)
async def grant_waiver(
    payload: ComplianceWaiverCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_WAIVE)),
) -> ComplianceWaiverOut:
    waiver = await compliance_service.grant_waiver(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    await session.refresh(waiver)
    return ComplianceWaiverOut.model_validate(waiver)


@router.get("/projects/{project_id}/waivers", response_model=List[ComplianceWaiverOut])
async def list_waivers_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_READ)),
) -> List[ComplianceWaiverOut]:
    waivers = await compliance_service.list_waivers_for_project(
        session, current_user.org_id, project_id
    )
    return [ComplianceWaiverOut.model_validate(w) for w in waivers]


@router.post("/waivers/{waiver_id}/revoke", response_model=ComplianceWaiverOut)
async def revoke_waiver(
    waiver_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.COMPLIANCE_WAIVE)),
) -> ComplianceWaiverOut:
    waiver = await compliance_service.revoke_waiver(
        session, current_user.org_id, waiver_id
    )
    await session.commit()
    return ComplianceWaiverOut.model_validate(waiver)
