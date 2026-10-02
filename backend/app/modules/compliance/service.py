"""
Solar Operations OS — Compliance Service
Orchestrates compliance runs by evaluating regulations/rules against project state.
Supports waivers and audit history.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.compliance.events import (
    ComplianceRunCompleted,
    ComplianceRunStarted,
    ComplianceWaiverGranted,
)
from app.modules.compliance.models import (
    ComplianceResult,
    ComplianceRun,
    ComplianceWaiver,
    ResultStatus,
    RunStatus,
)
from app.modules.compliance.public import ComplianceRunTrigger, ComplianceWaiverCreate
from app.modules.regulations.models import Rule, RuleSet
from app.modules.regulations.service import regulations_service


class ComplianceService:
    async def run_compliance(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        trigger: ComplianceRunTrigger,
        actor_id: Optional[uuid.UUID] = None,
        event_name: Optional[str] = None,
    ) -> ComplianceRun:
        now = datetime.now(timezone.utc)

        # 1. Create run record
        run = ComplianceRun(
            organization_id=org_id,
            project_id=trigger.project_id,
            rule_set_id=trigger.rule_set_id,
            triggered_by_user_id=actor_id,
            triggered_by_event=event_name,
            status=RunStatus.RUNNING,
            started_at=now,
            context_snapshot=trigger.context_override,
        )
        session.add(run)
        await session.flush()

        await event_bus.publish(
            ComplianceRunStarted(
                organization_id=org_id,
                project_id=run.project_id,
                run_id=run.id,
                rule_set_id=run.rule_set_id,
            )
        )

        # 2. Determine rules to evaluate
        rules_to_run: List[Rule] = []
        if trigger.rule_set_id:
            rs = (
                await session.execute(
                    select(RuleSet).where(
                        RuleSet.organization_id == org_id,
                        RuleSet.id == trigger.rule_set_id,
                    )
                )
            ).scalar_one_or_none()
            if not rs:
                run.status = RunStatus.FAILED
                run.error_message = f"RuleSet {trigger.rule_set_id} not found"
                run.completed_at = datetime.now(timezone.utc)
                return run

            if rs.rule_ids:
                rule_uuids = [uuid.UUID(r_id) for r_id in rs.rule_ids]
                rules_to_run = list(
                    (
                        await session.execute(
                            select(Rule).where(
                                Rule.organization_id == org_id,
                                Rule.id.in_(rule_uuids),
                            )
                        )
                    ).scalars().all()
                )
        else:
            # Run all active rules
            rules_to_run = list(
                (
                    await session.execute(
                        select(Rule).where(
                            Rule.organization_id == org_id,
                            Rule.status == "active",
                        )
                    )
                ).scalars().all()
            )

        # 3. Fetch active waivers for project
        waivers = list(
            (
                await session.execute(
                    select(ComplianceWaiver).where(
                        ComplianceWaiver.organization_id == org_id,
                        ComplianceWaiver.project_id == trigger.project_id,
                        ComplianceWaiver.is_active == True,
                    )
                )
            ).scalars().all()
        )
        waiver_by_rule = {w.rule_code: w for w in waivers}

        # 4. Evaluate each rule
        passed_count = 0
        failed_count = 0
        warned_count = 0

        context = trigger.context_override

        for rule in rules_to_run:
            if rule.code in waiver_by_rule:
                waiver = waiver_by_rule[rule.code]
                result = ComplianceResult(
                    organization_id=org_id,
                    run_id=run.id,
                    rule_id=rule.id,
                    rule_code=rule.code,
                    rule_title=rule.title,
                    status=ResultStatus.WAIVED,
                    message=f"Waived: {waiver.reason}",
                    evidence={"waiver_id": str(waiver.id)},
                    waiver_id=waiver.id,
                )
                session.add(result)
                passed_count += 1
                continue

            eval_res = await regulations_service.evaluate_rule(
                session, org_id, rule.id, context
            )
            if eval_res.details.get("skipped"):
                status = ResultStatus.SKIPPED
            elif eval_res.passed:
                status = ResultStatus.PASS
                passed_count += 1
            else:
                status = ResultStatus.FAIL
                failed_count += 1

            result = ComplianceResult(
                organization_id=org_id,
                run_id=run.id,
                rule_id=rule.id,
                rule_code=rule.code,
                rule_title=rule.title,
                status=status,
                message=eval_res.reason,
                evidence=eval_res.details,
            )
            session.add(result)

        # 5. Finalize run stats
        run.total_rules = len(rules_to_run)
        run.passed = passed_count
        run.failed = failed_count
        run.warned = warned_count
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        await event_bus.publish(
            ComplianceRunCompleted(
                organization_id=org_id,
                project_id=run.project_id,
                run_id=run.id,
                passed=run.passed,
                failed=run.failed,
                warned=run.warned,
                total_rules=run.total_rules,
            )
        )
        return run

    async def get_run(
        self, session: AsyncSession, org_id: uuid.UUID, run_id: uuid.UUID
    ) -> ComplianceRun:
        run = (
            await session.execute(
                select(ComplianceRun)
                .options(selectinload(ComplianceRun.results))
                .where(
                    ComplianceRun.organization_id == org_id,
                    ComplianceRun.id == run_id,
                )
            )
        ).scalar_one_or_none()
        if not run:
            raise NotFoundError(f"ComplianceRun {run_id} not found")
        return run

    async def list_runs_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[ComplianceRun]:
        stmt = (
            select(ComplianceRun)
            .options(selectinload(ComplianceRun.results))
            .where(
                ComplianceRun.organization_id == org_id,
                ComplianceRun.project_id == project_id,
            )
            .order_by(ComplianceRun.created_at.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    # ── Waivers ───────────────────────────────────────────────────────────────
    async def grant_waiver(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: ComplianceWaiverCreate,
        actor_id: uuid.UUID,
    ) -> ComplianceWaiver:
        waiver = ComplianceWaiver(
            organization_id=org_id,
            project_id=data.project_id,
            rule_code=data.rule_code,
            reason=data.reason,
            granted_by_user_id=actor_id,
            granted_at=datetime.now(timezone.utc),
            expires_at=data.expires_at,
            is_active=True,
        )
        session.add(waiver)
        await event_bus.publish(
            ComplianceWaiverGranted(
                organization_id=org_id,
                project_id=waiver.project_id,
                waiver_id=waiver.id,
                rule_code=waiver.rule_code,
                granted_by_user_id=actor_id,
            )
        )
        return waiver

    async def list_waivers_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[ComplianceWaiver]:
        stmt = select(ComplianceWaiver).where(
            ComplianceWaiver.organization_id == org_id,
            ComplianceWaiver.project_id == project_id,
        )
        return list((await session.execute(stmt)).scalars().all())

    async def revoke_waiver(
        self, session: AsyncSession, org_id: uuid.UUID, waiver_id: uuid.UUID
    ) -> ComplianceWaiver:
        waiver = (
            await session.execute(
                select(ComplianceWaiver).where(
                    ComplianceWaiver.organization_id == org_id,
                    ComplianceWaiver.id == waiver_id,
                )
            )
        ).scalar_one_or_none()
        if not waiver:
            raise NotFoundError(f"Waiver {waiver_id} not found")
        waiver.is_active = False
        return waiver


compliance_service = ComplianceService()
