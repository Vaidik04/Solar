"""
Solar Operations OS — O&M Module Router
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.oam.public import (
    MaintenancePlanCreate,
    MaintenancePlanOut,
    MaintenanceTaskOut,
    SLAPolicyCreate,
    SLAPolicyOut,
    TicketCreate,
    TicketOut,
    TicketUpdate,
    VisitCreate,
    VisitOut,
    VisitUpdate,
)
from app.modules.oam.service import oam_service

router = APIRouter(prefix="/oam", tags=["O&M"])


# ── SLA Policies ──────────────────────────────────────────────────────────────
@router.post(
    "/sla-policies",
    response_model=SLAPolicyOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_sla_policy(
    payload: SLAPolicyCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> SLAPolicyOut:
    policy = await oam_service.create_sla_policy(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(policy)
    return SLAPolicyOut.model_validate(policy)


@router.get("/sla-policies", response_model=List[SLAPolicyOut])
async def list_sla_policies(
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> List[SLAPolicyOut]:
    items = await oam_service.list_sla_policies(session, current_user.org_id)
    return [SLAPolicyOut.model_validate(i) for i in items]


# ── Maintenance Plans & Tasks ─────────────────────────────────────────────────
@router.post(
    "/plans",
    response_model=MaintenancePlanOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_maintenance_plan(
    payload: MaintenancePlanCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> MaintenancePlanOut:
    plan = await oam_service.create_maintenance_plan(session, current_user.org_id, payload)
    await session.commit()
    full_plan = await oam_service.get_maintenance_plan(session, current_user.org_id, plan.id)
    return MaintenancePlanOut.model_validate(full_plan)


@router.get("/plans/{plan_id}", response_model=MaintenancePlanOut)
async def get_maintenance_plan(
    plan_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> MaintenancePlanOut:
    plan = await oam_service.get_maintenance_plan(session, current_user.org_id, plan_id)
    return MaintenancePlanOut.model_validate(plan)


@router.get("/projects/{project_id}/plans", response_model=List[MaintenancePlanOut])
async def list_plans_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> List[MaintenancePlanOut]:
    plans = await oam_service.list_plans_for_project(session, current_user.org_id, project_id)
    return [MaintenancePlanOut.model_validate(p) for p in plans]


@router.post("/tasks/{task_id}/complete", response_model=MaintenanceTaskOut)
async def complete_maintenance_task(
    task_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_PLAN_MANAGE)),
) -> MaintenanceTaskOut:
    task = await oam_service.complete_task(session, current_user.org_id, task_id)
    await session.commit()
    await session.refresh(task)
    return MaintenanceTaskOut.model_validate(task)


# ── Tickets ───────────────────────────────────────────────────────────────────
@router.post(
    "/tickets",
    response_model=TicketOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    payload: TicketCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_TICKET_CREATE)),
) -> TicketOut:
    ticket = await oam_service.create_ticket(
        session, current_user.org_id, payload, actor_id=current_user.id
    )
    await session.commit()
    full_ticket = await oam_service.get_ticket(session, current_user.org_id, ticket.id)
    return TicketOut.model_validate(full_ticket)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_TICKET_CREATE)),
) -> TicketOut:
    ticket = await oam_service.get_ticket(session, current_user.org_id, ticket_id)
    return TicketOut.model_validate(ticket)


@router.get("/tickets", response_model=List[TicketOut])
async def list_tickets(
    project_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_TICKET_CREATE)),
) -> List[TicketOut]:
    items = await oam_service.list_tickets(
        session, current_user.org_id, project_id=project_id, status=status
    )
    return [TicketOut.model_validate(t) for t in items]


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_TICKET_ASSIGN)),
) -> TicketOut:
    ticket = await oam_service.update_ticket(
        session, current_user.org_id, ticket_id, payload, actor_id=current_user.id
    )
    await session.commit()
    full_ticket = await oam_service.get_ticket(session, current_user.org_id, ticket.id)
    return TicketOut.model_validate(full_ticket)


# ── Visits ────────────────────────────────────────────────────────────────────
@router.post(
    "/visits",
    response_model=VisitOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_visit(
    payload: VisitCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_VISIT_MANAGE)),
) -> VisitOut:
    visit = await oam_service.create_visit(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(visit)
    return VisitOut.model_validate(visit)


@router.patch("/visits/{visit_id}", response_model=VisitOut)
async def update_visit(
    visit_id: uuid.UUID,
    payload: VisitUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_VISIT_MANAGE)),
) -> VisitOut:
    visit = await oam_service.update_visit(session, current_user.org_id, visit_id, payload)
    await session.commit()
    await session.refresh(visit)
    return VisitOut.model_validate(visit)


@router.get("/projects/{project_id}/visits", response_model=List[VisitOut])
async def list_visits_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.OAM_VISIT_MANAGE)),
) -> List[VisitOut]:
    items = await oam_service.list_visits_for_project(session, current_user.org_id, project_id)
    return [VisitOut.model_validate(v) for v in items]
