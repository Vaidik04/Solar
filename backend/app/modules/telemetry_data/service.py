"""
Solar Operations OS — Telemetry Service
Handles Inverter registration, data source polling config, generation time-series ingestion,
telemetry alarms, and plant outages.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.telemetry_data.events import (
    AlarmTriggered,
    GenerationIngested,
    InverterRegistered,
)
from app.modules.telemetry_data.models import (
    AlarmStatus,
    DataSourceConfig,
    GenerationRecord,
    InverterDevice,
    Outage,
    TelemetryAlarm,
)
from app.modules.telemetry_data.public import (
    GenerationRecordCreate,
    GenerationSummaryOut,
    InverterCreate,
    OutageCreate,
    TelemetryAlarmCreate,
)


class TelemetryService:
    # ── Inverters & Data Source ───────────────────────────────────────────────
    async def register_inverter(
        self, session: AsyncSession, org_id: uuid.UUID, data: InverterCreate
    ) -> InverterDevice:
        existing = (
            await session.execute(
                select(InverterDevice).where(
                    InverterDevice.organization_id == org_id,
                    InverterDevice.serial_number == data.serial_number,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Inverter with serial number '{data.serial_number}' already exists")

        inverter = InverterDevice(
            organization_id=org_id,
            project_id=data.project_id,
            plant_id=data.plant_id,
            asset_id=data.asset_id,
            make=data.make,
            model=data.model,
            serial_number=data.serial_number,
            rated_capacity_kw=data.rated_capacity_kw,
            device_specs=data.device_specs,
        )
        session.add(inverter)
        await session.flush()

        if data.data_source:
            ds = DataSourceConfig(
                organization_id=org_id,
                inverter_id=inverter.id,
                protocol=data.data_source.protocol,
                host=data.data_source.host,
                port=data.data_source.port,
                unit_id=data.data_source.unit_id,
                poll_interval_seconds=data.data_source.poll_interval_seconds,
                connection_params=data.data_source.connection_params,
            )
            session.add(ds)

        await event_bus.publish(
            InverterRegistered(
                organization_id=org_id,
                project_id=inverter.project_id,
                inverter_id=inverter.id,
                serial_number=inverter.serial_number,
            )
        )
        return inverter

    async def get_inverter(
        self, session: AsyncSession, org_id: uuid.UUID, inverter_id: uuid.UUID
    ) -> InverterDevice:
        inverter = (
            await session.execute(
                select(InverterDevice)
                .options(selectinload(InverterDevice.data_source))
                .where(
                    InverterDevice.organization_id == org_id,
                    InverterDevice.id == inverter_id,
                )
            )
        ).scalar_one_or_none()
        if not inverter:
            raise NotFoundError(f"Inverter {inverter_id} not found")
        return inverter

    async def list_inverters_for_project(
        self, session: AsyncSession, org_id: uuid.UUID, project_id: uuid.UUID
    ) -> List[InverterDevice]:
        stmt = (
            select(InverterDevice)
            .options(selectinload(InverterDevice.data_source))
            .where(
                InverterDevice.organization_id == org_id,
                InverterDevice.project_id == project_id,
            )
        )
        return list((await session.execute(stmt)).scalars().all())

    # ── Generation Records ────────────────────────────────────────────────────
    async def ingest_generation_record(
        self, session: AsyncSession, org_id: uuid.UUID, data: GenerationRecordCreate
    ) -> GenerationRecord:
        rec = GenerationRecord(
            organization_id=org_id,
            inverter_id=data.inverter_id,
            plant_id=data.plant_id,
            recorded_at=data.recorded_at,
            interval_minutes=data.interval_minutes,
            energy_kwh=data.energy_kwh,
            peak_power_kw=data.peak_power_kw,
            avg_power_kw=data.avg_power_kw,
            grid_voltage_v=data.grid_voltage_v,
            grid_frequency_hz=data.grid_frequency_hz,
            power_factor=data.power_factor,
            irradiance_wm2=data.irradiance_wm2,
            module_temp_c=data.module_temp_c,
            ambient_temp_c=data.ambient_temp_c,
            raw_payload=data.raw_payload,
        )
        session.add(rec)
        await event_bus.publish(
            GenerationIngested(
                organization_id=org_id,
                plant_id=rec.plant_id,
                inverter_id=rec.inverter_id,
                energy_kwh=float(rec.energy_kwh),
                recorded_at=str(rec.recorded_at),
            )
        )
        return rec

    async def get_plant_generation_summary(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        plant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> GenerationSummaryOut:
        stmt = select(
            func.coalesce(func.sum(GenerationRecord.energy_kwh), 0.0),
            func.max(GenerationRecord.peak_power_kw),
            func.avg(GenerationRecord.avg_power_kw),
            func.count(GenerationRecord.id),
        ).where(
            GenerationRecord.organization_id == org_id,
            GenerationRecord.plant_id == plant_id,
        )
        if start_time:
            stmt = stmt.where(GenerationRecord.recorded_at >= start_time)
        if end_time:
            stmt = stmt.where(GenerationRecord.recorded_at <= end_time)

        row = (await session.execute(stmt)).one()
        total_kwh, peak_kw, avg_kw, count = row
        return GenerationSummaryOut(
            plant_id=plant_id,
            total_energy_kwh=float(total_kwh),
            peak_power_kw=float(peak_kw) if peak_kw is not None else None,
            avg_power_kw=float(avg_kw) if avg_kw is not None else None,
            records_count=int(count),
        )

    async def list_generation_records(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        plant_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[GenerationRecord]:
        stmt = (
            select(GenerationRecord)
            .where(
                GenerationRecord.organization_id == org_id,
                GenerationRecord.plant_id == plant_id,
            )
            .order_by(GenerationRecord.recorded_at.desc())
            .limit(limit)
        )
        if start_time:
            stmt = stmt.where(GenerationRecord.recorded_at >= start_time)
        if end_time:
            stmt = stmt.where(GenerationRecord.recorded_at <= end_time)
        return list((await session.execute(stmt)).scalars().all())

    # ── Alarms ────────────────────────────────────────────────────────────────
    async def create_alarm(
        self, session: AsyncSession, org_id: uuid.UUID, data: TelemetryAlarmCreate
    ) -> TelemetryAlarm:
        alarm = TelemetryAlarm(
            organization_id=org_id,
            inverter_id=data.inverter_id,
            plant_id=data.plant_id,
            alarm_code=data.alarm_code,
            severity=data.severity,
            status=AlarmStatus.ACTIVE,
            description=data.description,
            occurred_at=data.occurred_at,
        )
        session.add(alarm)
        await event_bus.publish(
            AlarmTriggered(
                organization_id=org_id,
                plant_id=alarm.plant_id,
                inverter_id=alarm.inverter_id,
                alarm_id=alarm.id,
                alarm_code=alarm.alarm_code,
                severity=alarm.severity,
            )
        )
        return alarm

    async def acknowledge_alarm(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        alarm_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> TelemetryAlarm:
        alarm = (
            await session.execute(
                select(TelemetryAlarm).where(
                    TelemetryAlarm.organization_id == org_id,
                    TelemetryAlarm.id == alarm_id,
                )
            )
        ).scalar_one_or_none()
        if not alarm:
            raise NotFoundError(f"Alarm {alarm_id} not found")

        alarm.status = AlarmStatus.ACKNOWLEDGED
        alarm.acknowledged_at = datetime.now(timezone.utc)
        alarm.acknowledged_by_user_id = actor_id
        return alarm

    async def resolve_alarm(
        self, session: AsyncSession, org_id: uuid.UUID, alarm_id: uuid.UUID
    ) -> TelemetryAlarm:
        alarm = (
            await session.execute(
                select(TelemetryAlarm).where(
                    TelemetryAlarm.organization_id == org_id,
                    TelemetryAlarm.id == alarm_id,
                )
            )
        ).scalar_one_or_none()
        if not alarm:
            raise NotFoundError(f"Alarm {alarm_id} not found")

        alarm.status = AlarmStatus.RESOLVED
        alarm.resolved_at = datetime.now(timezone.utc)
        return alarm

    async def list_alarms(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        plant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[TelemetryAlarm]:
        stmt = (
            select(TelemetryAlarm)
            .where(TelemetryAlarm.organization_id == org_id)
            .order_by(TelemetryAlarm.occurred_at.desc())
        )
        if plant_id:
            stmt = stmt.where(TelemetryAlarm.plant_id == plant_id)
        if status:
            stmt = stmt.where(TelemetryAlarm.status == status)
        return list((await session.execute(stmt)).scalars().all())

    # ── Outages ───────────────────────────────────────────────────────────────
    async def record_outage(
        self, session: AsyncSession, org_id: uuid.UUID, data: OutageCreate
    ) -> Outage:
        outage = Outage(
            organization_id=org_id,
            plant_id=data.plant_id,
            project_id=data.project_id,
            outage_start=data.outage_start,
            outage_end=data.outage_end,
            estimated_loss_kwh=data.estimated_loss_kwh,
            cause=data.cause,
            linked_ticket_id=data.linked_ticket_id,
            is_resolved=data.outage_end is not None,
        )
        session.add(outage)
        return outage

    async def resolve_outage(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        outage_id: uuid.UUID,
        outage_end: datetime,
        estimated_loss_kwh: Optional[float] = None,
    ) -> Outage:
        outage = (
            await session.execute(
                select(Outage).where(
                    Outage.organization_id == org_id, Outage.id == outage_id
                )
            )
        ).scalar_one_or_none()
        if not outage:
            raise NotFoundError(f"Outage {outage_id} not found")

        outage.outage_end = outage_end
        outage.is_resolved = True
        if estimated_loss_kwh is not None:
            outage.estimated_loss_kwh = estimated_loss_kwh
        return outage

    async def list_outages(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        plant_id: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> List[Outage]:
        stmt = select(Outage).where(Outage.organization_id == org_id).order_by(Outage.outage_start.desc())
        if plant_id:
            stmt = stmt.where(Outage.plant_id == plant_id)
        if project_id:
            stmt = stmt.where(Outage.project_id == project_id)
        return list((await session.execute(stmt)).scalars().all())


telemetry_service = TelemetryService()
