"""
Solar Operations OS — Telemetry Module Router
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.telemetry_data.public import (
    GenerationRecordCreate,
    GenerationRecordOut,
    GenerationSummaryOut,
    InverterCreate,
    InverterOut,
    OutageCreate,
    OutageOut,
    TelemetryAlarmCreate,
    TelemetryAlarmOut,
)
from app.modules.telemetry_data.service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


class ResolveOutageRequest(BaseModel):
    outage_end: datetime
    estimated_loss_kwh: Optional[float] = None


# ── Inverters ─────────────────────────────────────────────────────────────────
@router.post(
    "/inverters",
    response_model=InverterOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_inverter(
    payload: InverterCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_CONNECTOR_MANAGE)),
) -> InverterOut:
    inverter = await telemetry_service.register_inverter(session, current_user.org_id, payload)
    await session.commit()
    full_inverter = await telemetry_service.get_inverter(session, current_user.org_id, inverter.id)
    return InverterOut.model_validate(full_inverter)


@router.get("/inverters/{inverter_id}", response_model=InverterOut)
async def get_inverter(
    inverter_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> InverterOut:
    item = await telemetry_service.get_inverter(session, current_user.org_id, inverter_id)
    return InverterOut.model_validate(item)


@router.get("/projects/{project_id}/inverters", response_model=List[InverterOut])
async def list_inverters_for_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> List[InverterOut]:
    items = await telemetry_service.list_inverters_for_project(
        session, current_user.org_id, project_id
    )
    return [InverterOut.model_validate(i) for i in items]


# ── Generation Records ────────────────────────────────────────────────────────
@router.post(
    "/generation",
    response_model=GenerationRecordOut,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_generation(
    payload: GenerationRecordCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_CONNECTOR_MANAGE)),
) -> GenerationRecordOut:
    record = await telemetry_service.ingest_generation_record(
        session, current_user.org_id, payload
    )
    await session.commit()
    await session.refresh(record)
    return GenerationRecordOut.model_validate(record)


@router.get("/generation/summary", response_model=GenerationSummaryOut)
async def get_generation_summary(
    plant_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> GenerationSummaryOut:
    return await telemetry_service.get_plant_generation_summary(
        session, current_user.org_id, plant_id, start_time=start_time, end_time=end_time
    )


@router.get("/generation", response_model=List[GenerationRecordOut])
async def list_generation_records(
    plant_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> List[GenerationRecordOut]:
    items = await telemetry_service.list_generation_records(
        session,
        current_user.org_id,
        plant_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return [GenerationRecordOut.model_validate(i) for i in items]


# ── Alarms ────────────────────────────────────────────────────────────────────
@router.post(
    "/alarms",
    response_model=TelemetryAlarmOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_alarm(
    payload: TelemetryAlarmCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_CONNECTOR_MANAGE)),
) -> TelemetryAlarmOut:
    alarm = await telemetry_service.create_alarm(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(alarm)
    return TelemetryAlarmOut.model_validate(alarm)


@router.post("/alarms/{alarm_id}/acknowledge", response_model=TelemetryAlarmOut)
async def acknowledge_alarm(
    alarm_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> TelemetryAlarmOut:
    alarm = await telemetry_service.acknowledge_alarm(
        session, current_user.org_id, alarm_id, actor_id=current_user.id
    )
    await session.commit()
    await session.refresh(alarm)
    return TelemetryAlarmOut.model_validate(alarm)


@router.post("/alarms/{alarm_id}/resolve", response_model=TelemetryAlarmOut)
async def resolve_alarm(
    alarm_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> TelemetryAlarmOut:
    alarm = await telemetry_service.resolve_alarm(session, current_user.org_id, alarm_id)
    await session.commit()
    await session.refresh(alarm)
    return TelemetryAlarmOut.model_validate(alarm)


@router.get("/alarms", response_model=List[TelemetryAlarmOut])
async def list_alarms(
    plant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> List[TelemetryAlarmOut]:
    items = await telemetry_service.list_alarms(
        session, current_user.org_id, plant_id=plant_id, status=status
    )
    return [TelemetryAlarmOut.model_validate(i) for i in items]


# ── Outages ───────────────────────────────────────────────────────────────────
@router.post(
    "/outages",
    response_model=OutageOut,
    status_code=status.HTTP_201_CREATED,
)
async def record_outage(
    payload: OutageCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_CONNECTOR_MANAGE)),
) -> OutageOut:
    outage = await telemetry_service.record_outage(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(outage)
    return OutageOut.model_validate(outage)


@router.post("/outages/{outage_id}/resolve", response_model=OutageOut)
async def resolve_outage(
    outage_id: uuid.UUID,
    payload: ResolveOutageRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_CONNECTOR_MANAGE)),
) -> OutageOut:
    outage = await telemetry_service.resolve_outage(
        session,
        current_user.org_id,
        outage_id,
        outage_end=payload.outage_end,
        estimated_loss_kwh=payload.estimated_loss_kwh,
    )
    await session.commit()
    await session.refresh(outage)
    return OutageOut.model_validate(outage)


@router.get("/outages", response_model=List[OutageOut])
async def list_outages(
    plant_id: Optional[str] = Query(None),
    project_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.TELEMETRY_READ)),
) -> List[OutageOut]:
    items = await telemetry_service.list_outages(
        session, current_user.org_id, plant_id=plant_id, project_id=project_id
    )
    return [OutageOut.model_validate(i) for i in items]
