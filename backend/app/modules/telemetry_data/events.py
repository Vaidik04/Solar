"""
Solar Operations OS — Telemetry Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class InverterRegistered:
    event_type: str = field(default="telemetry.inverter.registered", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    inverter_id: uuid.UUID = uuid.UUID(int=0)
    serial_number: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GenerationIngested:
    event_type: str = field(default="telemetry.generation.ingested", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    inverter_id: uuid.UUID = uuid.UUID(int=0)
    energy_kwh: float = 0.0
    recorded_at: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AlarmTriggered:
    event_type: str = field(default="telemetry.alarm.triggered", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    inverter_id: uuid.UUID = uuid.UUID(int=0)
    alarm_id: uuid.UUID = uuid.UUID(int=0)
    alarm_code: str = ""
    severity: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
