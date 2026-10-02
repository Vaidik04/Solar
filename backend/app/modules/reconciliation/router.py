"""
Solar Operations OS — Reconciliation Module Router
"""
from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.reconciliation.public import (
    ReconciliationComparisonOut,
    ReconciliationRunCreate,
    ReconciliationRunOut,
    ResolveDiscrepancyRequest,
)
from app.modules.reconciliation.service import reconciliation_service

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post(
    "/runs",
    response_model=ReconciliationRunOut,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_reconciliation_run(
    payload: ReconciliationRunCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.RECONCILIATION_RUN)),
) -> ReconciliationRunOut:
    run = await reconciliation_service.run_reconciliation(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    full_run = await reconciliation_service.get_run(session, current_user.org_id, run.id)
    return ReconciliationRunOut.model_validate(full_run)


@router.get("/runs/{run_id}", response_model=ReconciliationRunOut)
async def get_reconciliation_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.RECONCILIATION_READ)),
) -> ReconciliationRunOut:
    run = await reconciliation_service.get_run(session, current_user.org_id, run_id)
    return ReconciliationRunOut.model_validate(run)


@router.get("/projects/{project_id}/runs", response_model=List[ReconciliationRunOut])
async def list_reconciliation_runs(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.RECONCILIATION_READ)),
) -> List[ReconciliationRunOut]:
    runs = await reconciliation_service.list_runs_for_project(
        session, current_user.org_id, project_id
    )
    return [ReconciliationRunOut.model_validate(r) for r in runs]


@router.post(
    "/comparisons/{comparison_id}/resolve",
    response_model=ReconciliationComparisonOut,
)
async def resolve_comparison_discrepancy(
    comparison_id: uuid.UUID,
    payload: ResolveDiscrepancyRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.RECONCILIATION_RUN)),
) -> ReconciliationComparisonOut:
    comp = await reconciliation_service.resolve_discrepancy(
        session, current_user.org_id, comparison_id, payload, actor_id=current_user.id
    )
    await session.commit()
    await session.refresh(comp)
    return ReconciliationComparisonOut.model_validate(comp)
