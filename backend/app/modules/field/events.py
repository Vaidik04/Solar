"""
Solar Operations OS — Field Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MeterRegistered:
    event_type: str = field(default="field.meter.registered", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    meter_id: uuid.UUID = uuid.UUID(int=0)
    serial_number: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InspectionScheduled:
    event_type: str = field(default="field.inspection.scheduled", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    inspection_id: uuid.UUID = uuid.UUID(int=0)
    scheduled_date: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InspectionCompleted:
    event_type: str = field(default="field.inspection.completed", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    inspection_id: uuid.UUID = uuid.UUID(int=0)
    overall_result: str = ""
    score_percent: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WCRSubmitted:
    event_type: str = field(default="field.wcr.submitted", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    wcr_id: uuid.UUID = uuid.UUID(int=0)
    wcr_number: str = ""
    capacity_installed_kw: float = 0.0
    document_sha256: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PlantCommissioned:
    event_type: str = field(default="field.plant.commissioned", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    commissioned_date: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
