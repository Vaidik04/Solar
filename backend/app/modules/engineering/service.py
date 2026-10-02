"""
Solar Operations OS — Engineering Service Interface
Manages Designs, BOMs, and String Configurations per project.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.engineering.events import BOMFinalised, DesignApproved, DesignCreated, DesignRevised
from app.modules.engineering.models import BOM, BOMItem, BOMStatus, Design, DesignStatus, StringConfiguration
from app.modules.engineering.public import BOMCreate, DesignCreate, DesignUpdate


class EngineeringService:
    # ── Design Operations ─────────────────────────────────────────────────────
    async def create_design(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: DesignCreate,
        actor_id: uuid.UUID,
    ) -> Design:
        # Determine next version
        stmt = select(Design).where(
            Design.organization_id == org_id,
            Design.project_id == data.project_id,
        ).order_by(Design.design_version.desc()).limit(1)
        last = (await session.execute(stmt)).scalar_one_or_none()
        version = (last.design_version + 1) if last else 1

        design = Design(
            organization_id=org_id,
            project_id=data.project_id,
            design_version=version,
            name=data.name,
            system_type=data.system_type,
            status=DesignStatus.DRAFT,
            capacity_kw_dc=data.capacity_kw_dc,
            capacity_kw_ac=data.capacity_kw_ac,
            panel_make=data.panel_make,
            panel_model=data.panel_model,
            panel_wattage=data.panel_wattage,
            panel_count=data.panel_count,
            inverter_make=data.inverter_make,
            inverter_model=data.inverter_model,
            inverter_count=data.inverter_count,
            tilt_degrees=data.tilt_degrees,
            azimuth_degrees=data.azimuth_degrees,
            expected_annual_generation_kwh=data.expected_annual_generation_kwh,
            performance_ratio_percent=data.performance_ratio_percent,
            notes=data.notes,
        )
        session.add(design)
        await session.flush()

        # String configurations
        for sc in data.string_configurations:
            session.add(StringConfiguration(
                organization_id=org_id,
                design_id=design.id,
                **sc.model_dump(),
            ))

        await session.flush()
        await event_bus.publish(DesignCreated(
            organization_id=org_id,
            project_id=data.project_id,
            design_id=design.id,
            design_version=version,
            capacity_kw_dc=float(data.capacity_kw_dc),
            system_type=data.system_type,
        ))
        return design

    async def approve_design(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        design_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> Design:
        design = await self._get_design(session, org_id, design_id)
        if design.status == DesignStatus.APPROVED:
            raise ConflictError("Design already approved")
        design.status = DesignStatus.APPROVED
        design.approved_by_user_id = actor_id
        design.approved_at = datetime.now(timezone.utc)
        session.add(design)
        await event_bus.publish(DesignApproved(
            organization_id=org_id,
            project_id=design.project_id,
            design_id=design_id,
            approved_by_user_id=actor_id,
        ))
        return design

    async def list_designs(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> List[Design]:
        stmt = select(Design).where(
            Design.organization_id == org_id,
            Design.project_id == project_id,
            Design.deleted_at.is_(None),
        ).order_by(Design.design_version.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_design(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        design_id: uuid.UUID,
    ) -> Design:
        return await self._get_design(session, org_id, design_id)

    # ── BOM Operations ────────────────────────────────────────────────────────
    async def create_bom(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: BOMCreate,
        actor_id: uuid.UUID,
    ) -> BOM:
        # Verify design exists
        design = await self._get_design(session, org_id, data.design_id)
        if design.project_id != data.project_id:
            raise ValidationError("Design does not belong to the given project")

        stmt = select(BOM).where(
            BOM.organization_id == org_id,
            BOM.project_id == data.project_id,
        ).order_by(BOM.bom_version.desc()).limit(1)
        last_bom = (await session.execute(stmt)).scalar_one_or_none()
        version = (last_bom.bom_version + 1) if last_bom else 1

        bom = BOM(
            organization_id=org_id,
            project_id=data.project_id,
            design_id=data.design_id,
            bom_version=version,
            status=BOMStatus.DRAFT,
        )
        session.add(bom)
        await session.flush()

        for item_data in data.items:
            session.add(BOMItem(
                organization_id=org_id,
                bom_id=bom.id,
                **item_data.model_dump(),
            ))

        await session.flush()
        return bom

    async def finalize_bom(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        bom_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> BOM:
        bom = await self._get_bom(session, org_id, bom_id)
        if bom.status == BOMStatus.LOCKED:
            raise ConflictError("BOM is already locked")
        bom.status = BOMStatus.FINALIZED
        bom.finalized_at = datetime.now(timezone.utc)
        bom.finalized_by_user_id = actor_id
        session.add(bom)

        # Count items
        item_stmt = select(BOMItem).where(BOMItem.bom_id == bom_id)
        items = (await session.execute(item_stmt)).scalars().all()

        await event_bus.publish(BOMFinalised(
            organization_id=org_id,
            project_id=bom.project_id,
            bom_id=bom_id,
            bom_version=bom.bom_version,
            item_count=len(items),
        ))
        return bom

    async def get_bom(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        bom_id: uuid.UUID,
    ) -> BOM:
        bom = await self._get_bom(session, org_id, bom_id)
        # Eager-load items
        stmt = select(BOM).where(
            BOM.id == bom_id,
            BOM.organization_id == org_id,
        ).options(selectinload(BOM.items))
        result = await session.execute(stmt)
        return result.scalar_one_or_none() or bom

    # ── Internals ─────────────────────────────────────────────────────────────
    async def _get_design(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        design_id: uuid.UUID,
    ) -> Design:
        stmt = select(Design).where(
            Design.id == design_id,
            Design.organization_id == org_id,
            Design.deleted_at.is_(None),
        )
        design = (await session.execute(stmt)).scalar_one_or_none()
        if not design:
            raise NotFoundError("Design", str(design_id))
        return design

    async def _get_bom(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        bom_id: uuid.UUID,
    ) -> BOM:
        stmt = select(BOM).where(
            BOM.id == bom_id,
            BOM.organization_id == org_id,
        )
        bom = (await session.execute(stmt)).scalar_one_or_none()
        if not bom:
            raise NotFoundError("BOM", str(bom_id))
        return bom


engineering_service = EngineeringService()
