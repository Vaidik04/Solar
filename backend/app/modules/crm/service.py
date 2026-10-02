"""
Solar Operations OS — CRM & Sites Module Service
The ONLY entry point for business logic and queries on customers and sites.
Emits domain events and persists them to the transactional outbox.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.core.storage import get_storage_service
from app.modules.crm.events import (
    CustomerCreated,
    CustomerUpdated,
    SiteCreated,
    SiteSurveyCompleted,
    SiteUpdated,
)
from app.modules.crm.models import (
    Contact,
    Customer,
    CustomerType,
    KycStatus,
    PhotoCategory,
    Site,
    SitePhoto,
    SiteSurvey,
    SurveyStatus,
)
from app.modules.crm.public import (
    CustomerCreate,
    CustomerUpdate,
    SiteCreate,
    SiteSurveyCreate,
    SiteUpdate,
)


class CrmService:
    # ── Customer Operations ───────────────────────────────────────────────────
    async def create_customer(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: CustomerCreate,
    ) -> Customer:
        # Check for duplicate phone within organization
        stmt = select(Customer).where(
            Customer.organization_id == org_id,
            Customer.phone == data.phone,
            Customer.deleted_at.is_(None),
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Customer with phone number {data.phone} already exists in organization")

        customer = Customer(
            organization_id=org_id,
            customer_type=data.customer_type,
            name=data.name,
            company_name=data.company_name,
            email=str(data.email) if data.email else None,
            phone=data.phone,
            alternate_phone=data.alternate_phone,
            pan_number=data.pan_number,
            gst_number=data.gst_number,
            billing_address=data.billing_address,
            notes=data.notes,
        )
        session.add(customer)
        await session.flush()

        # Add initial contacts if provided
        for contact_data in data.contacts:
            contact = Contact(
                organization_id=org_id,
                customer_id=customer.id,
                name=contact_data.name,
                designation=contact_data.designation,
                email=str(contact_data.email) if contact_data.email else None,
                phone=contact_data.phone,
                is_primary=contact_data.is_primary,
            )
            session.add(contact)

        # Buffer outbox event
        await event_bus.emit_to_outbox(
            session,
            CustomerCreated(
                organization_id=org_id,
                customer_id=customer.id,
                customer_type=customer.customer_type,
                name=customer.name,
                phone=customer.phone,
            ),
        )

        return customer

    async def get_customer(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        customer_id: uuid.UUID,
    ) -> Customer:
        stmt = (
            select(Customer)
            .where(
                Customer.id == customer_id,
                Customer.organization_id == org_id,
                Customer.deleted_at.is_(None),
            )
            .options(selectinload(Customer.contacts))
        )
        customer = (await session.execute(stmt)).scalar_one_or_none()
        if not customer:
            raise NotFoundError("Customer", str(customer_id))
        return customer

    async def list_customers(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        query: Optional[str] = None,
    ) -> Tuple[List[Customer], int]:
        base_stmt = select(Customer).where(
            Customer.organization_id == org_id,
            Customer.deleted_at.is_(None),
        )
        if query:
            base_stmt = base_stmt.where(
                (Customer.name.ilike(f"%{query}%"))
                | (Customer.phone.ilike(f"%{query}%"))
                | (Customer.email.ilike(f"%{query}%"))
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        list_stmt = (
            base_stmt.order_by(Customer.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Customer.contacts))
        )
        result = (await session.execute(list_stmt)).scalars().all()
        return list(result), total

    async def update_customer(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        customer_id: uuid.UUID,
        data: CustomerUpdate,
    ) -> Customer:
        customer = await self.get_customer(session, org_id, customer_id)
        update_data = data.model_dump(exclude_unset=True)

        for field_name, value in update_data.items():
            if field_name == "email" and value is not None:
                value = str(value)
            setattr(customer, field_name, value)

        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            CustomerUpdated(
                organization_id=org_id,
                customer_id=customer.id,
                name=customer.name,
                kyc_status=customer.kyc_status,
            ),
        )
        return customer

    # ── Site Operations ───────────────────────────────────────────────────────
    async def create_site(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: SiteCreate,
    ) -> Site:
        # Validate that customer exists in tenant
        await self.get_customer(session, org_id, data.customer_id)

        site = Site(
            organization_id=org_id,
            customer_id=data.customer_id,
            branch_id=data.branch_id,
            name=data.name,
            address=data.address,
            state_code=data.state_code.upper(),
            pincode=data.pincode,
            latitude=data.latitude,
            longitude=data.longitude,
            discom_name=data.discom_name,
            consumer_number=data.consumer_number,
            meter_number=data.meter_number,
            sanctioned_load_kw=data.sanctioned_load_kw,
            tariff_category=data.tariff_category,
            transformer_capacity_kva=data.transformer_capacity_kva,
            supply_voltage_kv=data.supply_voltage_kv,
            roof_type=data.roof_type,
            usable_roof_area_sqft=data.usable_roof_area_sqft,
            tilt_angle_degrees=data.tilt_angle_degrees,
            azimuth_degrees=data.azimuth_degrees,
            shading_hazards=data.shading_hazards or {},
        )
        session.add(site)
        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            SiteCreated(
                organization_id=org_id,
                site_id=site.id,
                customer_id=site.customer_id,
                name=site.name,
                state_code=site.state_code,
                pincode=site.pincode,
                sanctioned_load_kw=float(site.sanctioned_load_kw),
            ),
        )
        return site

    async def get_site(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        site_id: uuid.UUID,
    ) -> Site:
        stmt = (
            select(Site)
            .where(
                Site.id == site_id,
                Site.organization_id == org_id,
                Site.deleted_at.is_(None),
            )
            .options(
                selectinload(Site.customer),
                selectinload(Site.surveys),
                selectinload(Site.photos),
            )
        )
        site = (await session.execute(stmt)).scalar_one_or_none()
        if not site:
            raise NotFoundError("Site", str(site_id))
        return site

    async def list_sites(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        branch_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Site], int]:
        stmt = select(Site).where(
            Site.organization_id == org_id,
            Site.deleted_at.is_(None),
        )
        if customer_id:
            stmt = stmt.where(Site.customer_id == customer_id)
        if branch_id:
            stmt = stmt.where(Site.branch_id == branch_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        list_stmt = stmt.order_by(Site.created_at.desc()).offset(offset).limit(limit)
        result = (await session.execute(list_stmt)).scalars().all()
        return list(result), total

    # ── Site Survey Operations ────────────────────────────────────────────────
    async def create_survey(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        site_id: uuid.UUID,
        data: SiteSurveyCreate,
    ) -> SiteSurvey:
        site = await self.get_site(session, org_id, site_id)

        survey = SiteSurvey(
            organization_id=org_id,
            site_id=site.id,
            surveyor_user_id=data.surveyor_user_id,
            survey_date=data.survey_date,
            status=SurveyStatus.COMPLETED,
            structural_viability=data.structural_viability,
            recommended_capacity_kw=data.recommended_capacity_kw,
            electrical_assessment=data.electrical_assessment,
            shadow_analysis=data.shadow_analysis,
            gps_verified=data.gps_verified,
            survey_coordinates=data.survey_coordinates,
            notes=data.notes,
        )
        session.add(survey)
        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            SiteSurveyCompleted(
                organization_id=org_id,
                survey_id=survey.id,
                site_id=site.id,
                surveyor_user_id=survey.surveyor_user_id,
                recommended_capacity_kw=float(survey.recommended_capacity_kw) if survey.recommended_capacity_kw else None,
                structural_viability=survey.structural_viability,
            ),
        )
        return survey

    # ── Site Photo Operations (Content-Addressed Storage) ─────────────────────
    async def upload_site_photo(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        site_id: uuid.UUID,
        uploader_user_id: uuid.UUID,
        photo_bytes: bytes,
        filename: str,
        category: PhotoCategory,
        mime_type: str = "image/jpeg",
        survey_id: Optional[uuid.UUID] = None,
        caption: Optional[str] = None,
        exif_lat: Optional[float] = None,
        exif_lon: Optional[float] = None,
        exif_captured_at: Optional[datetime] = None,
        compass_bearing: Optional[float] = None,
    ) -> SitePhoto:
        site = await self.get_site(session, org_id, site_id)

        # Upload bytes to storage with SHA-256 content address
        storage = get_storage_service()
        content_hash, storage_key = storage.upload_bytes(
            organization_id=org_id,
            data=photo_bytes,
            filename=filename,
            content_type=mime_type,
        )

        photo = SitePhoto(
            organization_id=org_id,
            site_id=site.id,
            survey_id=survey_id,
            uploader_user_id=uploader_user_id,
            category=category,
            caption=caption,
            storage_key=storage_key,
            sha256_hash=content_hash,
            file_size_bytes=len(photo_bytes),
            mime_type=mime_type,
            exif_latitude=exif_lat,
            exif_longitude=exif_lon,
            exif_captured_at=exif_captured_at,
            compass_bearing_degrees=compass_bearing,
        )
        session.add(photo)
        await session.flush()
        return photo


crm_service = CrmService()
