"""
Solar Operations OS — Telemetry Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Inverters & Data Source ───────────────────────────────────────────────────
class DataSourceConfigCreate(BaseModel):
    protocol: str = Field("modbus_tcp", max_length=50)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = None
    unit_id: Optional[int] = None
    poll_interval_seconds: int = Field(300, ge=10)
    connection_params: Dict[str, Any] = Field(default_factory=dict)


class DataSourceConfigOut(BaseModel):
    id: uuid.UUID
    inverter_id: uuid.UUID
    protocol: str
    host: Optional[str] = None
    port: Optional[int] = None
    unit_id: Optional[int] = None
    poll_interval_seconds: int
    connection_params: Dict[str, Any]
    is_active: bool
    last_polled_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InverterCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    asset_id: Optional[uuid.UUID] = None
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    serial_number: str = Field(..., max_length=100)
    rated_capacity_kw: float = Field(..., gt=0)
    device_specs: Dict[str, Any] = Field(default_factory=dict)
    data_source: Optional[DataSourceConfigCreate] = None


class InverterOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    asset_id: Optional[uuid.UUID] = None
    make: str
    model: str
    serial_number: str
    rated_capacity_kw: float
    is_active: bool
    device_specs: Dict[str, Any]
    data_source: Optional[DataSourceConfigOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Generation Records ────────────────────────────────────────────────────────
class GenerationRecordCreate(BaseModel):
    inverter_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    recorded_at: datetime
    interval_minutes: int = Field(15, ge=1)
    energy_kwh: float = Field(..., ge=0)
    peak_power_kw: Optional[float] = None
    avg_power_kw: Optional[float] = None
    grid_voltage_v: Optional[float] = None
    grid_frequency_hz: Optional[float] = None
    power_factor: Optional[float] = None
    irradiance_wm2: Optional[float] = None
    module_temp_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    raw_payload: Optional[Dict[str, Any]] = None


class GenerationRecordOut(BaseModel):
    id: uuid.UUID
    inverter_id: uuid.UUID
    plant_id: str
    recorded_at: datetime
    interval_minutes: int
    energy_kwh: float
    peak_power_kw: Optional[float] = None
    avg_power_kw: Optional[float] = None
    grid_voltage_v: Optional[float] = None
    grid_frequency_hz: Optional[float] = None
    power_factor: Optional[float] = None
    irradiance_wm2: Optional[float] = None
    module_temp_c: Optional[float] = None
    ambient_temp_c: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GenerationSummaryOut(BaseModel):
    plant_id: str
    total_energy_kwh: float
    peak_power_kw: Optional[float] = None
    avg_power_kw: Optional[float] = None
    records_count: int


# ── Alarms ────────────────────────────────────────────────────────────────────
class TelemetryAlarmCreate(BaseModel):
    inverter_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    alarm_code: str = Field(..., max_length=100)
    severity: str = Field("warning", max_length=50)
    description: str = Field(..., min_length=3)
    occurred_at: datetime


class TelemetryAlarmOut(BaseModel):
    id: uuid.UUID
    inverter_id: uuid.UUID
    plant_id: str
    alarm_code: str
    severity: str
    status: str
    description: str
    occurred_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by_user_id: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Outages ───────────────────────────────────────────────────────────────────
class OutageCreate(BaseModel):
    plant_id: str = Field(..., max_length=50)
    project_id: uuid.UUID
    outage_start: datetime
    outage_end: Optional[datetime] = None
    estimated_loss_kwh: Optional[float] = None
    cause: Optional[str] = None
    linked_ticket_id: Optional[uuid.UUID] = None


class OutageOut(BaseModel):
    id: uuid.UUID
    plant_id: str
    project_id: uuid.UUID
    outage_start: datetime
    outage_end: Optional[datetime] = None
    estimated_loss_kwh: Optional[float] = None
    cause: Optional[str] = None
    is_resolved: bool
    linked_ticket_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
