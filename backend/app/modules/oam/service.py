"""
Solar Operations OS — O&M Service
Implements SLA policies, service tickets, maintenance plans/tasks, and technician visit dispatch.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.oam.events import (
    MaintenanceTaskCompleted,
    TicketAssigned,
    TicketCreated,
    TicketStatusChanged,
    VisitScheduled,
)
from app.modules.oam.models import (
    MaintenancePlan,
    MaintenanceTask,
    SLAPolicy,
    TaskFrequency,
    Ticket,
    TicketEvent,
    TicketPriority,
    TicketStatus,
    Visit,
    VisitStatus,
)
from app.modules.oam.public import (
    MaintenancePlanCreate,
    SLAPolicyCreate,
    TicketCreate,
    TicketUpdate,
    VisitCreate,
    VisitUpdate,
)


class OAMService:
    # ── SLA Policies ──────────────────────────────────────────────────────────
    async def create_sla_policy(
        self, session: AsyncSession, org_id: uuid.UUID, data: SLAPolicyCreate
    ) -> SLAPolicy:
        existing = (
            await session.execute(
                select(SLAPolicy).where(
                    SLAPolicy.organization_id == org_id, SLAPolicy.name == data.name
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"SLA Policy '{data.name}' already exists")

        policy = SLAPolicy(
            organization_id=org_id,
            name=data.name,
            priority=data.priority,
            first_response_hours=data.first_response_hours,
            resolution_hours=data.resolution_hours,
            escalation_hours=data.escalation_hours,
            is_default=data.is_default,
        )
        session.add(policy)
        return policy

    async def list_sla_policies(
        self, session: AsyncSession, org_id: uuid.UUID
    ) -> List[SLAPolicy]:
        stmt = select(SLAPolicy).where(SLAPolicy.organization_id == org_id)
        return list((await session.execute(stmt)).scalars().all())

    # ── Maintenance Plans ─────────────────────────────────────────────────────
    async def create_maintenance_plan(
        self, session: AsyncSession, org_id: uuid.UUID, data: MaintenancePlanCreate
    ) -> MaintenancePlan:
        plan = MaintenancePlan(
            organization_id=org_id,
            project_id=data.project_id,
            plant_id=data.plant_id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        session.add(plan)
        await session.flush()

        for t_data in data.tasks:
            task = MaintenanceTask(
                organization_id=org_id,
                plan_id=plan.id,
                title=t_data.title,
                category=t_data.category,
                frequency=t_data.frequency,
                estimated_duration_hours=t_data.estimated_duration_hours,
                checklist_template=t_data.checklist_template,
                assigned_team_id=t_data.assigned_team_id,
                next_due_date=t_data.next_due_date or data.start_date,
            )
            session.add(task)

        return plan

    async def get_maintenance_plan(
        self, session: AsyncSession, org_id: uuid.UUID, plan_id: uuid.UUID
    ) -> MaintenancePlan:
        plan = (
            await session.execute(
                select(MaintenancePlan)
                .options(selectinload(MaintenancePlan.tasks))
                .where(
                    MaintenancePlan.organization_id == org_id,
                    MaintenancePlan.id == plan_id,
                )
            )
        ).scalar_one_or_none()
        if not plan:
            raise NotFoundError(f"MaintenancePlan {plan_id} not found")
        return plan

    async def list_plans_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[MaintenancePlan]:
        stmt = (
            select(MaintenancePlan)
            .options(selectinload(MaintenancePlan.tasks))
            .where(
                MaintenancePlan.organization_id == org_id,
                MaintenancePlan.project_id == project_id,
            )
        )
        return list((await session.execute(stmt)).scalars().all())

    async def complete_task(
        self, session: AsyncSession, org_id: uuid.UUID, task_id: uuid.UUID
    ) -> MaintenanceTask:
        task = (
            await session.execute(
                select(MaintenanceTask).where(
                    MaintenanceTask.organization_id == org_id,
                    MaintenanceTask.id == task_id,
                )
            )
        ).scalar_one_or_none()
        if not task:
            raise NotFoundError(f"Task {task_id} not found")

        today = date.today()
        task.last_completed_date = today

        # Calculate next due date
        delta_days = 30
        if task.frequency == TaskFrequency.DAILY:
            delta_days = 1
        elif task.frequency == TaskFrequency.WEEKLY:
            delta_days = 7
        elif task.frequency == TaskFrequency.MONTHLY:
            delta_days = 30
        elif task.frequency == TaskFrequency.QUARTERLY:
            delta_days = 90
        elif task.frequency == TaskFrequency.HALF_YEARLY:
            delta_days = 180
        elif task.frequency == TaskFrequency.ANNUALLY:
            delta_days = 365

        task.next_due_date = today + timedelta(days=delta_days)

        await event_bus.publish(
            MaintenanceTaskCompleted(
                organization_id=org_id,
                task_id=task.id,
                plan_id=task.plan_id,
            )
        )
        return task

    # ── Service Tickets ───────────────────────────────────────────────────────
    async def create_ticket(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: TicketCreate,
        actor_id: uuid.UUID,
    ) -> Ticket:
        # Generate ticket number
        now = datetime.now(timezone.utc)
        count_stmt = select(Ticket).where(
            Ticket.organization_id == org_id, Ticket.project_id == data.project_id
        )
        existing_tickets = list((await session.execute(count_stmt)).scalars().all())
        ticket_number = f"TKT-{data.plant_id}-{len(existing_tickets) + 1:04d}"

        # Match SLA policy
        sla_stmt = select(SLAPolicy).where(
            SLAPolicy.organization_id == org_id,
            SLAPolicy.priority == data.priority,
        )
        sla = (await session.execute(sla_stmt)).scalar_one_or_none()

        first_resp_due = now + timedelta(hours=sla.first_response_hours) if sla else None
        res_due = now + timedelta(hours=sla.resolution_hours) if sla else None

        ticket = Ticket(
            organization_id=org_id,
            ticket_number=ticket_number,
            project_id=data.project_id,
            plant_id=data.plant_id,
            category=data.category,
            priority=data.priority,
            status=TicketStatus.OPEN,
            title=data.title,
            description=data.description,
            reporter_user_id=actor_id,
            assignee_user_id=data.assignee_user_id,
            sla_policy_id=sla.id if sla else None,
            first_response_due_at=first_resp_due,
            resolution_due_at=res_due,
            affected_asset_ids=data.affected_asset_ids,
            tags=data.tags,
        )
        session.add(ticket)
        await session.flush()

        # Add initial timeline event
        event = TicketEvent(
            organization_id=org_id,
            ticket_id=ticket.id,
            event_type="ticket_created",
            description=f"Ticket created: {data.title}",
            actor_user_id=actor_id,
            to_status=TicketStatus.OPEN,
            event_meta={"priority": data.priority, "category": data.category},
        )
        session.add(event)

        await event_bus.publish(
            TicketCreated(
                organization_id=org_id,
                project_id=ticket.project_id,
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                priority=ticket.priority,
            )
        )
        return ticket

    async def update_ticket(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        ticket_id: uuid.UUID,
        data: TicketUpdate,
        actor_id: uuid.UUID,
    ) -> Ticket:
        ticket = await self.get_ticket(session, org_id, ticket_id)
        now = datetime.now(timezone.utc)

        # Status transition
        if data.status and data.status != ticket.status:
            from_status = ticket.status
            ticket.status = data.status

            if from_status == TicketStatus.OPEN and not ticket.first_responded_at:
                ticket.first_responded_at = now

            if data.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                ticket.resolved_at = now

            session.add(
                TicketEvent(
                    organization_id=org_id,
                    ticket_id=ticket.id,
                    event_type="status_changed",
                    description=f"Status changed from {from_status} to {data.status}. {data.notes or ''}".strip(),
                    actor_user_id=actor_id,
                    from_status=from_status,
                    to_status=data.status,
                    event_meta={"notes": data.notes},
                )
            )
            await event_bus.publish(
                TicketStatusChanged(
                    organization_id=org_id,
                    ticket_id=ticket.id,
                    from_status=from_status,
                    to_status=data.status,
                )
            )

        # Assignee update
        if data.assignee_user_id and data.assignee_user_id != ticket.assignee_user_id:
            ticket.assignee_user_id = data.assignee_user_id
            session.add(
                TicketEvent(
                    organization_id=org_id,
                    ticket_id=ticket.id,
                    event_type="assigned",
                    description=f"Ticket assigned to user {data.assignee_user_id}",
                    actor_user_id=actor_id,
                    event_meta={"assignee_id": str(data.assignee_user_id)},
                )
            )
            await event_bus.publish(
                TicketAssigned(
                    organization_id=org_id,
                    ticket_id=ticket.id,
                    assignee_user_id=data.assignee_user_id,
                )
            )

        if data.priority:
            ticket.priority = data.priority

        return ticket

    async def get_ticket(
        self, session: AsyncSession, org_id: uuid.UUID, ticket_id: uuid.UUID
    ) -> Ticket:
        ticket = (
            await session.execute(
                select(Ticket)
                .options(selectinload(Ticket.ticket_events))
                .where(Ticket.organization_id == org_id, Ticket.id == ticket_id)
            )
        ).scalar_one_or_none()
        if not ticket:
            raise NotFoundError(f"Ticket {ticket_id} not found")
        return ticket

    async def list_tickets(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> List[Ticket]:
        stmt = (
            select(Ticket)
            .options(selectinload(Ticket.ticket_events))
            .where(Ticket.organization_id == org_id)
            .order_by(Ticket.created_at.desc())
        )
        if project_id:
            stmt = stmt.where(Ticket.project_id == project_id)
        if status:
            stmt = stmt.where(Ticket.status == status)
        return list((await session.execute(stmt)).scalars().all())

    # ── Visits ────────────────────────────────────────────────────────────────
    async def create_visit(
        self, session: AsyncSession, org_id: uuid.UUID, data: VisitCreate
    ) -> Visit:
        visit = Visit(
            organization_id=org_id,
            project_id=data.project_id,
            ticket_id=data.ticket_id,
            technician_user_id=data.technician_user_id,
            planned_date=data.planned_date,
            status=VisitStatus.PLANNED,
        )
        session.add(visit)
        await event_bus.publish(
            VisitScheduled(
                organization_id=org_id,
                visit_id=visit.id,
                project_id=visit.project_id,
                technician_user_id=visit.technician_user_id,
            )
        )
        return visit

    async def update_visit(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        visit_id: uuid.UUID,
        data: VisitUpdate,
    ) -> Visit:
        visit = (
            await session.execute(
                select(Visit).where(Visit.organization_id == org_id, Visit.id == visit_id)
            )
        ).scalar_one_or_none()
        if not visit:
            raise NotFoundError(f"Visit {visit_id} not found")

        if data.status:
            visit.status = data.status
        if data.arrived_at:
            visit.arrived_at = data.arrived_at
        if data.departed_at:
            visit.departed_at = data.departed_at
        if data.work_done_summary:
            visit.work_done_summary = data.work_done_summary
        if data.parts_used is not None:
            visit.parts_used = data.parts_used
        if data.geo_location:
            visit.geo_location = data.geo_location
        if data.photo_storage_keys is not None:
            visit.photo_storage_keys = data.photo_storage_keys

        return visit

    async def list_visits_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[Visit]:
        stmt = select(Visit).where(
            Visit.organization_id == org_id, Visit.project_id == project_id
        )
        return list((await session.execute(stmt)).scalars().all())


oam_service = OAMService()
