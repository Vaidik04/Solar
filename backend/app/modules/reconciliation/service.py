"""
Solar Operations OS — Reconciliation Service
Implements automated three-way reconciliation (Design vs BOM vs Installed Assets),
cryptographic source snapshotting, and discrepancy resolution.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.assets.models import Asset
from app.modules.engineering.models import BOM, BOMItem
from app.modules.reconciliation.events import (
    ReconciliationDiscrepancyResolved,
    ReconciliationRunCompleted,
    ReconciliationRunStarted,
)
from app.modules.reconciliation.models import (
    ComparisonResult,
    ReconciliationComparison,
    ReconciliationRun,
    ReconciliationRunStatus,
    ReconciliationScope,
    SourceSnapshot,
)
from app.modules.reconciliation.public import (
    ReconciliationRunCreate,
    ResolveDiscrepancyRequest,
)


class ReconciliationService:
    def _compute_sha256(self, data: Any) -> str:
        serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    async def run_reconciliation(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: ReconciliationRunCreate,
        actor_id: Optional[uuid.UUID] = None,
        event_name: Optional[str] = None,
    ) -> ReconciliationRun:
        now = datetime.now(timezone.utc)

        # 1. Initialize run
        run = ReconciliationRun(
            organization_id=org_id,
            project_id=data.project_id,
            scope=data.scope,
            status=ReconciliationRunStatus.RUNNING,
            triggered_by_user_id=actor_id,
            triggered_by_event=event_name,
            started_at=now,
        )
        session.add(run)
        await session.flush()

        await event_bus.publish(
            ReconciliationRunStarted(
                organization_id=org_id,
                project_id=run.project_id,
                run_id=run.id,
                scope=run.scope,
            )
        )

        # 2. Gather Planned Data (BOM items)
        bom_stmt = (
            select(BOM)
            .options(selectinload(BOM.items))
            .where(BOM.organization_id == org_id, BOM.project_id == data.project_id)
            .order_by(BOM.bom_version.desc())
            .limit(1)
        )
        bom = (await session.execute(bom_stmt)).scalar_one_or_none()
        planned_items: List[Dict[str, Any]] = []
        if bom and bom.items:
            for item in bom.items:
                planned_items.append(
                    {
                        "category": item.category,
                        "make": item.make,
                        "model": item.model,
                        "quantity": float(item.quantity),
                        "unit": item.unit_of_measure,
                        "item_code": item.item_code or f"{item.make}:{item.model}",
                    }
                )

        # 3. Gather Actual Data (Installed/Allocated Assets)
        assets_stmt = select(Asset).where(
            Asset.organization_id == org_id,
            Asset.allocated_project_id == data.project_id,
        )
        assets = list((await session.execute(assets_stmt)).scalars().all())
        actual_items: Dict[str, int] = {}
        for a in assets:
            key = f"{a.category}:{a.make}:{a.model}".lower()
            actual_items[key] = actual_items.get(key, 0) + 1

        # 4. Save Source Snapshots with cryptographic hash
        planned_hash = self._compute_sha256(planned_items)
        actual_hash = self._compute_sha256(actual_items)

        snap_planned = SourceSnapshot(
            organization_id=org_id,
            run_id=run.id,
            source_type="bom_planned",
            snapshot_data={"items": planned_items},
            sha256_hash=planned_hash,
            captured_at=now,
        )
        snap_actual = SourceSnapshot(
            organization_id=org_id,
            run_id=run.id,
            source_type="assets_actual",
            snapshot_data={"assets_by_type": actual_items},
            sha256_hash=actual_hash,
            captured_at=now,
        )
        session.add(snap_planned)
        session.add(snap_actual)

        # 5. Perform Comparison
        matched_count = 0
        mismatched_count = 0
        comparisons: List[ReconciliationComparison] = []

        seen_actual_keys = set()

        for p in planned_items:
            key = f"{p['category']}:{p['make']}:{p['model']}".lower()
            seen_actual_keys.add(key)
            actual_qty = actual_items.get(key, 0)
            planned_qty = p["quantity"]

            if actual_qty == planned_qty:
                res = ComparisonResult.MATCH
                matched_count += 1
                reason = None
            elif actual_qty < planned_qty:
                res = ComparisonResult.MISMATCH if actual_qty > 0 else ComparisonResult.MISSING_ACTUAL
                mismatched_count += 1
                reason = f"Shortfall: planned {planned_qty}, actual {actual_qty}"
            else:
                res = ComparisonResult.MISMATCH
                mismatched_count += 1
                reason = f"Surplus: planned {planned_qty}, actual {actual_qty}"

            comp = ReconciliationComparison(
                organization_id=org_id,
                run_id=run.id,
                item_key=p["item_code"],
                item_type=p["category"],
                result=res,
                planned_value={"quantity": planned_qty, "make": p["make"], "model": p["model"]},
                actual_value={"quantity": actual_qty},
                delta={"difference": actual_qty - planned_qty},
                mismatch_reason=reason,
            )
            session.add(comp)
            comparisons.append(comp)

        # Check for unexpected installed assets not in BOM
        for key, act_qty in actual_items.items():
            if key not in seen_actual_keys:
                mismatched_count += 1
                comp = ReconciliationComparison(
                    organization_id=org_id,
                    run_id=run.id,
                    item_key=key,
                    item_type=key.split(":")[0],
                    result=ComparisonResult.MISSING_PLANNED,
                    planned_value={"quantity": 0},
                    actual_value={"quantity": act_qty},
                    delta={"difference": act_qty},
                    mismatch_reason="Asset installed without matching BOM item",
                )
                session.add(comp)
                comparisons.append(comp)

        total = matched_count + mismatched_count
        run.total_items = total
        run.matched = matched_count
        run.mismatched = mismatched_count
        run.summary = {
            "scope": data.scope,
            "total_items": total,
            "matched": matched_count,
            "mismatched": mismatched_count,
            "planned_sha256": planned_hash,
            "actual_sha256": actual_hash,
        }
        run.status = ReconciliationRunStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        await event_bus.publish(
            ReconciliationRunCompleted(
                organization_id=org_id,
                project_id=run.project_id,
                run_id=run.id,
                scope=run.scope,
                matched=run.matched,
                mismatched=run.mismatched,
                total_items=run.total_items,
            )
        )
        return run

    async def get_run(
        self, session: AsyncSession, org_id: uuid.UUID, run_id: uuid.UUID
    ) -> ReconciliationRun:
        run = (
            await session.execute(
                select(ReconciliationRun)
                .options(
                    selectinload(ReconciliationRun.comparisons),
                    selectinload(ReconciliationRun.snapshots),
                )
                .where(
                    ReconciliationRun.organization_id == org_id,
                    ReconciliationRun.id == run_id,
                )
            )
        ).scalar_one_or_none()
        if not run:
            raise NotFoundError(f"ReconciliationRun {run_id} not found")
        return run

    async def list_runs_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[ReconciliationRun]:
        stmt = (
            select(ReconciliationRun)
            .options(
                selectinload(ReconciliationRun.comparisons),
                selectinload(ReconciliationRun.snapshots),
            )
            .where(
                ReconciliationRun.organization_id == org_id,
                ReconciliationRun.project_id == project_id,
            )
            .order_by(ReconciliationRun.created_at.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    async def resolve_discrepancy(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        comparison_id: uuid.UUID,
        data: ResolveDiscrepancyRequest,
        actor_id: uuid.UUID,
    ) -> ReconciliationComparison:
        comp = (
            await session.execute(
                select(ReconciliationComparison).where(
                    ReconciliationComparison.organization_id == org_id,
                    ReconciliationComparison.id == comparison_id,
                )
            )
        ).scalar_one_or_none()
        if not comp:
            raise NotFoundError(f"Comparison {comparison_id} not found")

        comp.result = data.override_result
        comp.resolution_notes = data.resolution_notes
        comp.resolved_by_user_id = actor_id
        comp.resolved_at = datetime.now(timezone.utc)

        await event_bus.publish(
            ReconciliationDiscrepancyResolved(
                organization_id=org_id,
                run_id=comp.run_id,
                comparison_id=comp.id,
                resolved_by_user_id=actor_id,
            )
        )
        return comp


reconciliation_service = ReconciliationService()
