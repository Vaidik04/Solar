"""
Solar Operations OS — Asset Registry Service
Guarantees:
- Normalized serial numbers and cross-tenant isolation
- Opaque, tamper-evident HMAC QR tokens
- Full 25-year lifecycle event lineage
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
from app.core.security import sign_qr_token, verify_qr_token
from app.modules.assets.events import (
    AssetAllocated,
    AssetInstalled,
    AssetRegistered,
    AssetReplaced,
    AssetRetired,
)
from app.modules.assets.models import (
    Asset,
    AssetCategory,
    AssetEvent,
    AssetEventType,
    AssetStatus,
    AssetType,
)
from app.modules.assets.normalizer import normalize_serial
from app.modules.assets.public import (
    AssetAllocate,
    AssetInstall,
    AssetRegister,
    AssetReplace,
    AssetTypeCreate,
)
from app.modules.project.models import Project


class AssetService:
    # ── Asset Type ────────────────────────────────────────────────────────────
    async def create_asset_type(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: AssetTypeCreate,
    ) -> AssetType:
        stmt = select(AssetType).where(
            AssetType.organization_id == org_id,
            AssetType.category == data.category,
            AssetType.make == data.make,
            AssetType.model == data.model,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        asset_type = AssetType(
            organization_id=org_id,
            category=data.category,
            make=data.make,
            model=data.model,
            nominal_rating_kw=data.nominal_rating_kw,
            warranty_months=data.warranty_months,
            is_serialized=data.is_serialized,
            specifications=data.specifications,
        )
        session.add(asset_type)
        await session.flush()
        return asset_type

    # ── Asset Lifecycle ───────────────────────────────────────────────────────
    async def register_asset(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID],
        data: AssetRegister,
    ) -> Asset:
        norm_serial = normalize_serial(data.serial_number)

        # Check for duplicate serial within tenant
        stmt = select(Asset).where(
            Asset.organization_id == org_id,
            Asset.normalized_serial == norm_serial,
            Asset.deleted_at.is_(None),
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Asset with serial '{data.serial_number}' is already registered")

        asset_id = uuid.uuid4()
        # Generate signed opaque HMAC QR token
        qr_token = sign_qr_token(asset_id, org_id)

        now = datetime.now(timezone.utc)
        asset = Asset(
            id=asset_id,
            organization_id=org_id,
            asset_type_id=data.asset_type_id,
            serial_number=data.serial_number.strip(),
            normalized_serial=norm_serial,
            qr_token=qr_token,
            status=AssetStatus.IN_STOCK,
            location_tag=data.location_tag,
            metadata_fields=data.metadata_fields,
        )
        session.add(asset)
        await session.flush()

        # Log initial event
        event = AssetEvent(
            organization_id=org_id,
            asset_id=asset.id,
            event_type=AssetEventType.REGISTERED,
            actor_user_id=actor_user_id,
            recorded_at=now,
            description="Asset registered into inventory",
            event_payload={"serial": norm_serial},
        )
        session.add(event)

        # Emit outbox event
        await event_bus.emit_to_outbox(
            session,
            AssetRegistered(
                organization_id=org_id,
                asset_id=asset.id,
                serial_number=norm_serial,
                asset_type_id=asset.asset_type_id,
            ),
        )
        return asset

    async def allocate_asset(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        asset_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID],
        data: AssetAllocate,
    ) -> Asset:
        asset = await self.get_asset(session, org_id, asset_id)
        if asset.status != AssetStatus.IN_STOCK:
            raise ValidationError(f"Cannot allocate asset with status '{asset.status}'")

        # Load project to obtain plant_id (Passport)
        proj_stmt = select(Project).where(
            Project.id == data.project_id,
            Project.organization_id == org_id,
        )
        project = (await session.execute(proj_stmt)).scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(data.project_id))

        now = datetime.now(timezone.utc)
        asset.project_id = project.id
        asset.plant_id = project.plant_id
        asset.status = AssetStatus.ALLOCATED
        if data.location_tag:
            asset.location_tag = data.location_tag

        event = AssetEvent(
            organization_id=org_id,
            asset_id=asset.id,
            event_type=AssetEventType.ALLOCATED,
            actor_user_id=actor_user_id,
            recorded_at=now,
            description=f"Allocated to Project {project.name} ({project.plant_id})",
            event_payload={"project_id": str(project.id), "plant_id": project.plant_id},
        )
        session.add(event)

        await event_bus.emit_to_outbox(
            session,
            AssetAllocated(
                organization_id=org_id,
                asset_id=asset.id,
                project_id=project.id,
                plant_id=project.plant_id,
            ),
        )
        return asset

    async def install_asset(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        asset_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID],
        data: AssetInstall,
    ) -> Asset:
        asset = await self.get_asset(session, org_id, asset_id)
        if asset.status not in (AssetStatus.ALLOCATED, AssetStatus.IN_STOCK):
            raise ValidationError(f"Cannot mark asset '{asset.status}' as installed")

        now = data.installed_at or datetime.now(timezone.utc)
        asset.status = AssetStatus.INSTALLED
        asset.location_tag = data.location_tag
        asset.installed_at = now

        event = AssetEvent(
            organization_id=org_id,
            asset_id=asset.id,
            event_type=AssetEventType.INSTALLED,
            actor_user_id=actor_user_id,
            recorded_at=now,
            description=f"Installed at location '{data.location_tag}'",
            event_payload={"location_tag": data.location_tag},
        )
        session.add(event)

        await event_bus.emit_to_outbox(
            session,
            AssetInstalled(
                organization_id=org_id,
                asset_id=asset.id,
                project_id=asset.project_id or uuid.UUID(int=0),
                plant_id=asset.plant_id or "",
                location_tag=data.location_tag,
            ),
        )
        return asset

    async def get_asset(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> Asset:
        stmt = (
            select(Asset)
            .where(
                Asset.id == asset_id,
                Asset.organization_id == org_id,
                Asset.deleted_at.is_(None),
            )
            .options(
                selectinload(Asset.asset_type),
                selectinload(Asset.events),
            )
        )
        asset = (await session.execute(stmt)).scalar_one_or_none()
        if not asset:
            raise NotFoundError("Asset", str(asset_id))
        return asset

    async def get_by_qr_token(
        self,
        session: AsyncSession,
        qr_token: str,
    ) -> Asset:
        # Verify HMAC cryptographic integrity first
        extracted = verify_qr_token(qr_token)
        if not extracted:
            raise ValidationError("Invalid or tampered QR token")

        asset_id, org_id = extracted
        return await self.get_asset(session, org_id, asset_id)


asset_service = AssetService()
