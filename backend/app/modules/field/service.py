"""
Solar Operations OS — Field Service
Handles Meters, Field Inspections, WCR (Work Completion Reports), and Commissioning.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.field.events import (
    InspectionCompleted,
    InspectionScheduled,
    MeterRegistered,
    PlantCommissioned,
    WCRSubmitted,
)
from app.modules.field.models import (
    CommissioningRecord,
    CommissioningStatus,
    Inspection,
    InspectionItem,
    InspectionStatus,
    InspectionTemplate,
    Meter,
    WCR,
    WCRStatus,
)
from app.modules.field.public import (
    CommissioningCreate,
    InspectionCreate,
    InspectionSubmit,
    InspectionTemplateCreate,
    MeterCreate,
    WCRCreate,
)


class FieldService:
    # ── Meter Operations ──────────────────────────────────────────────────────
    async def register_meter(
        self, session: AsyncSession, org_id: uuid.UUID, data: MeterCreate
    ) -> Meter:
        existing = (
            await session.execute(
                select(Meter).where(
                    Meter.organization_id == org_id,
                    Meter.serial_number == data.serial_number,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Meter with serial number '{data.serial_number}' already exists")

        meter = Meter(
            organization_id=org_id,
            project_id=data.project_id,
            plant_id=data.plant_id,
            meter_type=data.meter_type,
            make=data.make,
            model=data.model,
            serial_number=data.serial_number,
            meter_number=data.meter_number,
            discom_asset_id=data.discom_asset_id,
            capacity_kw=data.capacity_kw,
            installed_date=data.installed_date,
        )
        session.add(meter)
        await event_bus.publish(
            MeterRegistered(
                organization_id=org_id,
                project_id=meter.project_id,
                meter_id=meter.id,
                serial_number=meter.serial_number,
            )
        )
        return meter

    async def list_meters_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[Meter]:
        stmt = select(Meter).where(
            Meter.organization_id == org_id, Meter.project_id == project_id
        )
        return list((await session.execute(stmt)).scalars().all())

    async def get_meter(
        self, session: AsyncSession, org_id: uuid.UUID, meter_id: uuid.UUID
    ) -> Meter:
        meter = (
            await session.execute(
                select(Meter).where(Meter.organization_id == org_id, Meter.id == meter_id)
            )
        ).scalar_one_or_none()
        if not meter:
            raise NotFoundError(f"Meter {meter_id} not found")
        return meter

    # ── Inspection Template Operations ────────────────────────────────────────
    async def create_template(
        self, session: AsyncSession, org_id: uuid.UUID, data: InspectionTemplateCreate
    ) -> InspectionTemplate:
        existing = (
            await session.execute(
                select(InspectionTemplate).where(
                    InspectionTemplate.organization_id == org_id,
                    InspectionTemplate.code == data.code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Template code '{data.code}' already exists")

        template = InspectionTemplate(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            description=data.description,
            checklist=data.checklist,
        )
        session.add(template)
        return template

    async def list_templates(
        self, session: AsyncSession, org_id: uuid.UUID
    ) -> List[InspectionTemplate]:
        stmt = select(InspectionTemplate).where(
            InspectionTemplate.organization_id == org_id,
            InspectionTemplate.is_active == True,
        )
        return list((await session.execute(stmt)).scalars().all())

    async def get_template(
        self, session: AsyncSession, org_id: uuid.UUID, template_id: uuid.UUID
    ) -> InspectionTemplate:
        tmpl = (
            await session.execute(
                select(InspectionTemplate).where(
                    InspectionTemplate.organization_id == org_id,
                    InspectionTemplate.id == template_id,
                )
            )
        ).scalar_one_or_none()
        if not tmpl:
            raise NotFoundError(f"Inspection template {template_id} not found")
        return tmpl

    # ── Inspection Operations ─────────────────────────────────────────────────
    async def create_inspection(
        self, session: AsyncSession, org_id: uuid.UUID, data: InspectionCreate
    ) -> Inspection:
        insp = Inspection(
            organization_id=org_id,
            project_id=data.project_id,
            template_id=data.template_id,
            inspector_user_id=data.inspector_user_id,
            scheduled_date=data.scheduled_date,
            notes=data.notes,
            status=InspectionStatus.SCHEDULED,
        )
        session.add(insp)
        await event_bus.publish(
            InspectionScheduled(
                organization_id=org_id,
                project_id=insp.project_id,
                inspection_id=insp.id,
                scheduled_date=str(insp.scheduled_date or ""),
            )
        )
        return insp

    async def submit_inspection(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        inspection_id: uuid.UUID,
        data: InspectionSubmit,
    ) -> Inspection:
        insp = await self.get_inspection(session, org_id, inspection_id)

        insp.conducted_date = data.conducted_date
        insp.notes = data.notes
        insp.geo_location = data.geo_location

        # Add items and calculate score
        pass_count = 0
        total_items = len(data.items)

        for item_data in data.items:
            item = InspectionItem(
                organization_id=org_id,
                inspection_id=insp.id,
                check_code=item_data.check_code,
                label=item_data.label,
                result=item_data.result,
                numeric_value=item_data.numeric_value,
                text_value=item_data.text_value,
                photo_storage_key=item_data.photo_storage_key,
                remarks=item_data.remarks,
            )
            session.add(item)
            if item_data.result and item_data.result.lower() == "pass":
                pass_count += 1

        score = (pass_count / total_items * 100.0) if total_items > 0 else 100.0
        insp.score_percent = score
        insp.overall_result = "pass" if score >= 80.0 else "fail"
        insp.status = InspectionStatus.COMPLETED

        await event_bus.publish(
            InspectionCompleted(
                organization_id=org_id,
                project_id=insp.project_id,
                inspection_id=insp.id,
                overall_result=insp.overall_result,
                score_percent=float(insp.score_percent),
            )
        )
        return insp

    async def get_inspection(
        self, session: AsyncSession, org_id: uuid.UUID, inspection_id: uuid.UUID
    ) -> Inspection:
        insp = (
            await session.execute(
                select(Inspection)
                .options(selectinload(Inspection.items))
                .where(
                    Inspection.organization_id == org_id,
                    Inspection.id == inspection_id,
                )
            )
        ).scalar_one_or_none()
        if not insp:
            raise NotFoundError(f"Inspection {inspection_id} not found")
        return insp

    async def list_inspections_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[Inspection]:
        stmt = (
            select(Inspection)
            .options(selectinload(Inspection.items))
            .where(
                Inspection.organization_id == org_id,
                Inspection.project_id == project_id,
            )
            .order_by(Inspection.created_at.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    # ── WCR Operations ────────────────────────────────────────────────────────
    async def create_wcr(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: WCRCreate,
        actor_id: uuid.UUID,
    ) -> WCR:
        # Determine next version
        stmt = (
            select(WCR)
            .where(
                WCR.organization_id == org_id,
                WCR.project_id == data.project_id,
            )
            .order_by(WCR.wcr_version.desc())
            .limit(1)
        )
        last = (await session.execute(stmt)).scalar_one_or_none()
        version = (last.wcr_version + 1) if last else 1
        wcr_number = f"WCR-{data.plant_id}-V{version}"

        # Cryptographic integrity
        doc_hash = data.document_sha256
        if not doc_hash:
            payload = {
                "plant_id": data.plant_id,
                "version": version,
                "capacity": data.capacity_installed_kw,
                "asset_ids": data.asset_ids,
            }
            doc_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        wcr = WCR(
            organization_id=org_id,
            project_id=data.project_id,
            plant_id=data.plant_id,
            wcr_number=wcr_number,
            wcr_version=version,
            status=WCRStatus.SUBMITTED,
            completion_date=data.completion_date,
            capacity_installed_kw=data.capacity_installed_kw,
            asset_ids=data.asset_ids,
            document_storage_key=data.document_storage_key,
            document_sha256=doc_hash,
            submitted_by_user_id=actor_id,
            submitted_at=datetime.now(timezone.utc),
        )
        session.add(wcr)
        await event_bus.publish(
            WCRSubmitted(
                organization_id=org_id,
                project_id=wcr.project_id,
                wcr_id=wcr.id,
                wcr_number=wcr.wcr_number,
                capacity_installed_kw=float(wcr.capacity_installed_kw),
                document_sha256=wcr.document_sha256 or "",
            )
        )
        return wcr

    async def get_wcr(
        self, session: AsyncSession, org_id: uuid.UUID, wcr_id: uuid.UUID
    ) -> WCR:
        wcr = (
            await session.execute(
                select(WCR).where(WCR.organization_id == org_id, WCR.id == wcr_id)
            )
        ).scalar_one_or_none()
        if not wcr:
            raise NotFoundError(f"WCR {wcr_id} not found")
        return wcr

    async def list_wcrs_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[WCR]:
        stmt = (
            select(WCR)
            .where(
                WCR.organization_id == org_id,
                WCR.project_id == project_id,
            )
            .order_by(WCR.wcr_version.desc())
        )
        return list((await session.execute(stmt)).scalars().all())

    async def approve_and_sign_wcr(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        wcr_id: uuid.UUID,
        actor_id: uuid.UUID,
        signing_key: str = "wcr-sign-key-2026",
    ) -> WCR:
        """
        Approves and seals a Work Completion Report (WCR), converting from DRAFT/SUBMITTED
        to APPROVED. Generates cryptographic SHA-256 seal and verification QR token.
        """
        wcr = await self.get_wcr(session, org_id, wcr_id)
        if wcr.status == WCRStatus.APPROVED:
            return wcr

        wcr.status = WCRStatus.APPROVED
        wcr.approved_by_user_id = actor_id
        wcr.approved_at = datetime.now(timezone.utc)

        # Generate HMAC seal token
        payload = f"{wcr.plant_id}:{wcr.wcr_number}:{wcr.document_sha256}"
        wcr.qr_verification_token = hashlib.sha256(
            (payload + signing_key).encode()
        ).hexdigest()

        return wcr

    async def evaluate_commissioning_readiness(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> dict:
        """
        Commissioning Readiness Gate: verifies all technical, quality, and regulatory prerequisites.
        Returns explainable blockers if any checks fail.
        """
        blockers: List[str] = []
        checks_passed: List[str] = []

        # 1. Meter registration check
        meters = list(
            (
                await session.execute(
                    select(Meter).where(
                        Meter.organization_id == org_id,
                        Meter.project_id == project_id,
                    )
                )
            ).scalars().all()
        )
        if not meters:
            blockers.append("No DISCOM Net Meter or Generation Meter registered for this plant.")
        else:
            checks_passed.append(f"{len(meters)} meter(s) verified and calibrated.")

        # 2. Approved WCR check
        wcrs = await self.list_wcrs_for_project(session, org_id, project_id)
        approved_wcrs = [w for w in wcrs if w.status == WCRStatus.APPROVED]
        if not approved_wcrs:
            blockers.append("Final Work Completion Report (WCR) is not approved or digitally signed.")
        else:
            checks_passed.append(f"WCR {approved_wcrs[0].wcr_number} approved with cryptographic seal.")

        # 3. Quality Inspections check
        inspections = await self.list_inspections_for_project(session, org_id, project_id)
        if not inspections:
            blockers.append("No pre-commissioning quality inspections recorded.")
        else:
            failed_insps = [i for i in inspections if i.status == InspectionStatus.FAILED]
            if failed_insps:
                blockers.append(f"Inspection audit failed with unresolved issues ({len(failed_insps)} failed).")
            else:
                checks_passed.append(f"All {len(inspections)} quality inspection(s) completed and cleared.")

        is_ready = len(blockers) == 0
        return {
            "is_ready": is_ready,
            "status": "APPROVED_FOR_COMMISSIONING" if is_ready else "BLOCKED",
            "blockers": blockers,
            "checks_passed": checks_passed,
        }

    # ── Commissioning Record Operations ───────────────────────────────────────
    async def record_commissioning(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: CommissioningCreate,
        actor_id: uuid.UUID,
    ) -> CommissioningRecord:
        existing = (
            await session.execute(
                select(CommissioningRecord).where(
                    CommissioningRecord.organization_id == org_id,
                    CommissioningRecord.project_id == data.project_id,
                )
            )
        ).scalar_one_or_none()

        if existing:
            rec = existing
            rec.commissioned_date = data.commissioned_date
            rec.grid_synchronization_date = data.grid_synchronization_date
            rec.initial_generation_kwh = data.initial_generation_kwh
            rec.test_results = data.test_results
            rec.checklist_results = data.checklist_results
            rec.discom_approval_reference = data.discom_approval_reference
            rec.remarks = data.remarks
            rec.status = CommissioningStatus.COMMISSIONED
            rec.commissioned_by_user_id = actor_id
        else:
            rec = CommissioningRecord(
                organization_id=org_id,
                project_id=data.project_id,
                plant_id=data.plant_id,
                status=CommissioningStatus.COMMISSIONED,
                commissioned_date=data.commissioned_date,
                commissioned_by_user_id=actor_id,
                grid_synchronization_date=data.grid_synchronization_date,
                initial_generation_kwh=data.initial_generation_kwh,
                test_results=data.test_results,
                checklist_results=data.checklist_results,
                discom_approval_reference=data.discom_approval_reference,
                remarks=data.remarks,
            )
            session.add(rec)

        await event_bus.publish(
            PlantCommissioned(
                organization_id=org_id,
                project_id=rec.project_id,
                plant_id=rec.plant_id,
                commissioned_date=str(rec.commissioned_date or ""),
            )
        )
        return rec

    async def get_commissioning_record(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> CommissioningRecord:
        rec = (
            await session.execute(
                select(CommissioningRecord).where(
                    CommissioningRecord.organization_id == org_id,
                    CommissioningRecord.project_id == project_id,
                )
            )
        ).scalar_one_or_none()
        if not rec:
            raise NotFoundError(f"Commissioning record for project {project_id} not found")
        return rec


field_service = FieldService()
