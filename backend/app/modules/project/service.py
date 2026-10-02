"""
Solar Operations OS — Project Service Interface
Coordinates Project lifecycle, Plant ID allocation, Workflow transitions, and DISCOM applications.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.core.plant_id import allocate_plant_id
from app.modules.crm.models import Customer, Site
from app.modules.project.engine import workflow_engine
from app.modules.project.events import (
    DiscomApplicationSubmitted,
    ProjectCompleted,
    ProjectCreated,
    ProjectStageTransitioned,
)
from app.modules.project.models import (
    Application,
    DiscomAppStatus,
    Project,
    ProjectStage,
    ProjectStatus,
    StageHistory,
    WorkflowTransitionOverride,
)
from app.modules.project.public import (
    ApplicationCreate,
    ProjectCreate,
    ProjectTransition,
    ProjectTransitionOverride as ProjectTransitionOverrideSchema,
    ProjectUpdate,
)


class ProjectService:
    # ── Project Operations ────────────────────────────────────────────────────
    async def create_project(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: ProjectCreate,
    ) -> Project:
        # Validate Customer & Site exist within organization
        site_stmt = select(Site).where(
            Site.id == data.site_id,
            Site.organization_id == org_id,
            Site.deleted_at.is_(None),
        )
        site = (await session.execute(site_stmt)).scalar_one_or_none()
        if not site:
            raise NotFoundError("Site", str(data.site_id))

        # Allocate unique, sequential Digital Plant Passport ID
        plant_id = await allocate_plant_id(session, org_id, state_code=site.state_code)

        now = datetime.now(timezone.utc)
        project = Project(
            organization_id=org_id,
            plant_id=plant_id,
            name=data.name,
            customer_id=data.customer_id,
            site_id=data.site_id,
            branch_id=data.branch_id or site.branch_id,
            manager_user_id=data.manager_user_id,
            capacity_kw_dc=data.capacity_kw_dc,
            capacity_kw_ac=data.capacity_kw_ac,
            estimated_annual_kwh=data.estimated_annual_kwh,
            current_stage=ProjectStage.LEAD,
            status=ProjectStatus.ACTIVE,
            stage_entered_at=now,
            target_commissioning_date=data.target_commissioning_date,
            project_metadata=data.project_metadata,
        )
        session.add(project)
        await session.flush()

        # Record initial StageHistory
        initial_history = StageHistory(
            organization_id=org_id,
            project_id=project.id,
            from_stage="none",
            to_stage=ProjectStage.LEAD,
            transitioned_at=now,
            actor_user_id=data.manager_user_id,
            duration_in_stage_seconds=0,
            transition_reason="Project initiated",
            guard_results={"initial": True},
        )
        session.add(initial_history)

        # Buffer domain event to transactional outbox
        await event_bus.emit_to_outbox(
            session,
            ProjectCreated(
                organization_id=org_id,
                project_id=project.id,
                plant_id=project.plant_id,
                customer_id=project.customer_id,
                site_id=project.site_id,
                capacity_kw_dc=float(project.capacity_kw_dc),
                capacity_kw_ac=float(project.capacity_kw_ac),
            ),
        )

        return project

    async def get_project(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> Project:
        stmt = (
            select(Project)
            .where(
                Project.id == project_id,
                Project.organization_id == org_id,
                Project.deleted_at.is_(None),
            )
            .options(
                selectinload(Project.stage_histories),
                selectinload(Project.applications),
            )
        )
        project = (await session.execute(stmt)).scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))
        return project

    async def list_projects(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        stage: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
        site_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Project], int]:
        stmt = select(Project).where(
            Project.organization_id == org_id,
            Project.deleted_at.is_(None),
        )
        if stage:
            stmt = stmt.where(Project.current_stage == stage)
        if customer_id:
            stmt = stmt.where(Project.customer_id == customer_id)
        if site_id:
            stmt = stmt.where(Project.site_id == site_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        list_stmt = (
            stmt.order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Project.stage_histories))
        )
        result = (await session.execute(list_stmt)).scalars().all()
        return list(result), total

    # ── Stage Transition ──────────────────────────────────────────────────────
    async def transition_stage(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        transition: ProjectTransition,
        guard_context: Optional[Dict[str, Any]] = None,
    ) -> Project:
        project = await self.get_project(session, org_id, project_id)
        from_stage = project.current_stage
        to_stage = transition.to_stage

        # Evaluate guards via FSM Engine
        eval_result = workflow_engine.can_transition(from_stage, to_stage, guard_context)
        if not eval_result.allowed:
            raise ValidationError(
                f"Cannot transition project from '{from_stage}' to '{to_stage}': {'; '.join(eval_result.reasons)}"
            )

        now = datetime.now(timezone.utc)
        duration_seconds, _, _ = workflow_engine.calculate_stage_duration_and_sla(
            from_stage, project.stage_entered_at, now
        )

        project.current_stage = to_stage
        project.stage_entered_at = now

        if to_stage == ProjectStage.COMMISSIONING:
            project.actual_commissioning_date = now

        if to_stage in (ProjectStage.HANDOVER, ProjectStage.OAM_ACTIVE):
            project.status = ProjectStatus.COMPLETED

        # Record Stage History
        history = StageHistory(
            organization_id=org_id,
            project_id=project.id,
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_at=now,
            actor_user_id=actor_user_id,
            duration_in_stage_seconds=duration_seconds,
            transition_reason=transition.reason,
            guard_results={"guards": [g.__dict__ for g in eval_result.guard_evaluations]},
        )
        session.add(history)
        await session.flush()

        # Emit outbox event
        await event_bus.emit_to_outbox(
            session,
            ProjectStageTransitioned(
                organization_id=org_id,
                project_id=project.id,
                plant_id=project.plant_id,
                from_stage=from_stage,
                to_stage=to_stage,
                actor_user_id=actor_user_id,
                is_override=False,
            ),
        )

        return project

    # ── Stage Transition Override ─────────────────────────────────────────────
    async def override_transition(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
        approver_user_id: uuid.UUID,
        override_data: ProjectTransitionOverrideSchema,
    ) -> Project:
        """
        Bypasses normal guard checks with an audited human authorization.
        """
        project = await self.get_project(session, org_id, project_id)
        from_stage = project.current_stage
        to_stage = override_data.to_stage

        now = datetime.now(timezone.utc)
        duration_seconds, _, _ = workflow_engine.calculate_stage_duration_and_sla(
            from_stage, project.stage_entered_at, now
        )

        override_record = WorkflowTransitionOverride(
            organization_id=org_id,
            project_id=project.id,
            from_stage=from_stage,
            to_stage=to_stage,
            approved_by_user_id=approver_user_id,
            reason=override_data.reason,
            failed_guards={"override": True, "bypassed": True},
        )
        session.add(override_record)

        project.current_stage = to_stage
        project.stage_entered_at = now

        history = StageHistory(
            organization_id=org_id,
            project_id=project.id,
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_at=now,
            actor_user_id=approver_user_id,
            duration_in_stage_seconds=duration_seconds,
            transition_reason=f"OVERRIDE: {override_data.reason}",
            guard_results={"bypassed_by_override": True},
        )
        session.add(history)
        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            ProjectStageTransitioned(
                organization_id=org_id,
                project_id=project.id,
                plant_id=project.plant_id,
                from_stage=from_stage,
                to_stage=to_stage,
                actor_user_id=approver_user_id,
                is_override=True,
            ),
        )
        return project

    # ── DISCOM Applications ───────────────────────────────────────────────────
    async def create_application(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: ApplicationCreate,
    ) -> Application:
        await self.get_project(session, org_id, data.project_id)

        app = Application(
            organization_id=org_id,
            project_id=data.project_id,
            discom_name=data.discom_name,
            application_number=data.application_number,
            consumer_number=data.consumer_number,
            feeder_code=data.feeder_code,
            dt_code=data.dt_code,
            applied_capacity_kw=data.applied_capacity_kw,
            sanctioned_capacity_kw=data.sanctioned_capacity_kw,
            status=DiscomAppStatus.SUBMITTED,
            submission_date=datetime.now(timezone.utc),
            discom_fee_amount=data.discom_fee_amount,
            discom_fee_receipt_ref=data.discom_fee_receipt_ref,
            notes=data.notes,
        )
        session.add(app)
        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            DiscomApplicationSubmitted(
                organization_id=org_id,
                application_id=app.id,
                project_id=app.project_id,
                discom_name=app.discom_name,
                application_number=app.application_number,
            ),
        )
        return app


project_service = ProjectService()
