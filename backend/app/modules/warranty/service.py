"""
Solar Operations OS — Warranty Service
Handles Warranty registration, tracking, claims lifecycle, and timeline events.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.warranty.events import (
    WarrantyClaimOpened,
    WarrantyClaimStatusUpdated,
    WarrantyRegistered,
)
from app.modules.warranty.models import (
    ClaimEvent,
    ClaimStatus,
    Warranty,
    WarrantyClaim,
)
from app.modules.warranty.public import (
    WarrantyClaimCreate,
    WarrantyClaimStatusUpdate,
    WarrantyCreate,
)


class WarrantyService:
    # ── Warranty Management ───────────────────────────────────────────────────
    async def register_warranty(
        self, session: AsyncSession, org_id: uuid.UUID, data: WarrantyCreate
    ) -> Warranty:
        warranty = Warranty(
            organization_id=org_id,
            project_id=data.project_id,
            plant_id=data.plant_id,
            asset_id=data.asset_id,
            warranty_type=data.warranty_type,
            provider_name=data.provider_name,
            certificate_number=data.certificate_number,
            start_date=data.start_date,
            end_date=data.end_date,
            period_years=data.period_years,
            coverage_details=data.coverage_details,
            exclusions=data.exclusions,
            document_storage_key=data.document_storage_key,
            document_sha256=data.document_sha256,
        )
        session.add(warranty)
        await event_bus.publish(
            WarrantyRegistered(
                organization_id=org_id,
                project_id=warranty.project_id,
                warranty_id=warranty.id,
                warranty_type=warranty.warranty_type,
                provider_name=warranty.provider_name,
            )
        )
        return warranty

    async def get_warranty(
        self, session: AsyncSession, org_id: uuid.UUID, warranty_id: uuid.UUID
    ) -> Warranty:
        warranty = (
            await session.execute(
                select(Warranty).where(
                    Warranty.organization_id == org_id, Warranty.id == warranty_id
                )
            )
        ).scalar_one_or_none()
        if not warranty:
            raise NotFoundError(f"Warranty {warranty_id} not found")
        return warranty

    async def list_warranties_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[Warranty]:
        stmt = select(Warranty).where(
            Warranty.organization_id == org_id, Warranty.project_id == project_id
        )
        return list((await session.execute(stmt)).scalars().all())

    # ── Claims Management ─────────────────────────────────────────────────────
    async def open_claim(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: WarrantyClaimCreate,
        actor_id: uuid.UUID,
    ) -> WarrantyClaim:
        warranty = await self.get_warranty(session, org_id, data.warranty_id)

        # Count existing claims for numbering
        count_stmt = select(WarrantyClaim).where(
            WarrantyClaim.organization_id == org_id,
            WarrantyClaim.warranty_id == data.warranty_id,
        )
        existing_claims = list((await session.execute(count_stmt)).scalars().all())
        claim_number = f"CLM-{str(warranty.id)[:8]}-{len(existing_claims) + 1:03d}"

        today = date.today()
        claim = WarrantyClaim(
            organization_id=org_id,
            warranty_id=data.warranty_id,
            claim_number=claim_number,
            opened_date=today,
            status=ClaimStatus.OPENED,
            defect_description=data.defect_description,
            affected_components=data.affected_components,
            reported_by_user_id=actor_id,
        )
        session.add(claim)
        await session.flush()

        # Add initial timeline event
        event = ClaimEvent(
            organization_id=org_id,
            claim_id=claim.id,
            event_type="claim_opened",
            description=f"Claim opened: {data.defect_description[:100]}",
            actor_user_id=actor_id,
            event_meta={"initial_status": ClaimStatus.OPENED},
        )
        session.add(event)

        await event_bus.publish(
            WarrantyClaimOpened(
                organization_id=org_id,
                warranty_id=claim.warranty_id,
                claim_id=claim.id,
                claim_number=claim.claim_number,
            )
        )
        return claim

    async def update_claim_status(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        claim_id: uuid.UUID,
        data: WarrantyClaimStatusUpdate,
        actor_id: uuid.UUID,
    ) -> WarrantyClaim:
        claim = await self.get_claim(session, org_id, claim_id)

        old_status = claim.status
        claim.status = data.status

        if data.notes:
            claim.resolution_notes = data.notes

        if data.replacement_asset_ids is not None:
            claim.replacement_asset_ids = data.replacement_asset_ids

        if data.status.startswith("resolved_"):
            claim.resolved_date = date.today()

        event = ClaimEvent(
            organization_id=org_id,
            claim_id=claim.id,
            event_type=f"status_change_{data.status}",
            description=f"Claim status changed from {old_status} to {data.status}. {data.notes or ''}".strip(),
            actor_user_id=actor_id,
            event_meta={
                "old_status": old_status,
                "new_status": data.status,
                "notes": data.notes,
            },
        )
        session.add(event)

        await event_bus.publish(
            WarrantyClaimStatusUpdated(
                organization_id=org_id,
                claim_id=claim.id,
                claim_number=claim.claim_number,
                new_status=claim.status,
            )
        )
        return claim

    async def get_claim(
        self, session: AsyncSession, org_id: uuid.UUID, claim_id: uuid.UUID
    ) -> WarrantyClaim:
        claim = (
            await session.execute(
                select(WarrantyClaim)
                .options(selectinload(WarrantyClaim.events))
                .where(
                    WarrantyClaim.organization_id == org_id,
                    WarrantyClaim.id == claim_id,
                )
            )
        ).scalar_one_or_none()
        if not claim:
            raise NotFoundError(f"Claim {claim_id} not found")
        return claim

    async def list_claims_for_warranty(
        self, session: AsyncSession, org_id: uuid.UUID, warranty_id: uuid.UUID
    ) -> List[WarrantyClaim]:
        stmt = (
            select(WarrantyClaim)
            .options(selectinload(WarrantyClaim.events))
            .where(
                WarrantyClaim.organization_id == org_id,
                WarrantyClaim.warranty_id == warranty_id,
            )
            .order_by(WarrantyClaim.created_at.desc())
        )
        return list((await session.execute(stmt)).scalars().all())


warranty_service = WarrantyService()
