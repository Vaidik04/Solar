"""
Solar Operations OS — Project & Workflow Module: API Router
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.project.models import ProjectStage
from app.modules.project.public import (
    ApplicationCreate,
    ApplicationRead,
    ProjectCreate,
    ProjectRead,
    ProjectTransition,
    ProjectTransitionOverride,
    ProjectUpdate,
)
from app.modules.project.service import project_service

router = APIRouter(prefix="/projects", tags=["Projects & Workflow"])


# ── Project Endpoints ─────────────────────────────────────────────────────────
@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PROJECT_CREATE))],
)
async def create_project(
    data: ProjectCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectRead:
    project = await project_service.create_project(session, user.org_id, data)
    await session.commit()
    return ProjectRead.model_validate(project)


@router.get(
    "",
    response_model=List[ProjectRead],
    dependencies=[Depends(require_permission(Permission.PROJECT_READ))],
)
async def list_projects(
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    stage: Optional[ProjectStage] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    site_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[ProjectRead]:
    projects, _ = await project_service.list_projects(
        session, user.org_id, stage=stage, customer_id=customer_id, site_id=site_id, limit=limit, offset=offset
    )
    return [ProjectRead.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    dependencies=[Depends(require_permission(Permission.PROJECT_READ))],
)
async def get_project(
    project_id: uuid.UUID,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectRead:
    project = await project_service.get_project(session, user.org_id, project_id)
    return ProjectRead.model_validate(project)


@router.post(
    "/{project_id}/transition",
    response_model=ProjectRead,
    dependencies=[Depends(require_permission(Permission.PROJECT_TRANSITION))],
)
async def transition_stage(
    project_id: uuid.UUID,
    transition: ProjectTransition,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectRead:
    project = await project_service.transition_stage(
        session=session,
        org_id=user.org_id,
        project_id=project_id,
        actor_user_id=user.user_id,
        transition=transition,
    )
    await session.commit()
    return ProjectRead.model_validate(project)


@router.post(
    "/{project_id}/override",
    response_model=ProjectRead,
    dependencies=[Depends(require_permission(Permission.PROJECT_TRANSITION_OVERRIDE))],
)
async def override_transition(
    project_id: uuid.UUID,
    override_data: ProjectTransitionOverride,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectRead:
    project = await project_service.override_transition(
        session=session,
        org_id=user.org_id,
        project_id=project_id,
        approver_user_id=user.user_id,
        override_data=override_data,
    )
    await session.commit()
    return ProjectRead.model_validate(project)


# ── DISCOM Application Endpoints ──────────────────────────────────────────────
@router.post(
    "/{project_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.PROJECT_UPDATE))],
)
async def create_application(
    project_id: uuid.UUID,
    data: ApplicationCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationRead:
    data.project_id = project_id
    app = await project_service.create_application(session, user.org_id, data)
    await session.commit()
    return ApplicationRead.model_validate(app)
