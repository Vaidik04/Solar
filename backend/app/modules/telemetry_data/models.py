"""
Solar Operations OS — Telemetry Module: Database Models
Owns: InverterDevice, DataSourceConfig, GenerationRecord (hypertable), RawTelemetry (hypertable),
      TelemetryAlarm, Outage
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin


class DataSourceProtocol(StrEnum):
    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    SUNSPEC = "sunspec"
    API_PUSH = "api_push"
    MQTT = "mqtt"
    MANUAL = "manual"


class AlarmSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlarmStatus(StrEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


# ── Inverter Device ───────────────────────────────────────────────────────────
class InverterDevice(Base, TenantMixin, TimestampMixin):
    __tablename__ = "inverter_device"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset.id", ondelete="SET NULL"), nullable=True
    )
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False)
    rated_capacity_kw: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # MPPT inputs, string inputs, phase info
    device_specs: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    data_source: Mapped[Optional[DataSourceConfig]] = relationship(
        "DataSourceConfig", back_populates="inverter", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "serial_number", name="uq_inverter_serial"),
        Index("ix_inverter_project", "organization_id", "project_id"),
    )


# ── Data Source Config ────────────────────────────────────────────────────────
class DataSourceConfig(Base, TenantMixin, TimestampMixin):
    __tablename__ = "data_source_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inverter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    protocol: Mapped[str] = mapped_column(String(50), nullable=False)
    host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Modbus unit ID
    poll_interval_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    # Register map / topic / endpoint info
    connection_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_polled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    inverter: Mapped[InverterDevice] = relationship("InverterDevice", back_populates="data_source")


# ── Generation Record (TimescaleDB hypertable on recorded_at) ─────────────────
class GenerationRecord(Base, TenantMixin, TimestampMixin):
    """15-minute aggregate generation records. Will be converted to a TimescaleDB hypertable."""
    __tablename__ = "generation_record"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inverter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # Energy
    energy_kwh: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    peak_power_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)
    avg_power_kw: Mapped[Optional[float]] = mapped_column(Numeric(10, 3), nullable=True)

    # Grid metrics
    grid_voltage_v: Mapped[Optional[float]] = mapped_column(Numeric(7, 2), nullable=True)
    grid_frequency_hz: Mapped[Optional[float]] = mapped_column(Numeric(6, 3), nullable=True)
    power_factor: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)

    # Irradiance / weather (if available)
    irradiance_wm2: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    module_temp_c: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    ambient_temp_c: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)

    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("inverter_id", "recorded_at", "interval_minutes", name="uq_gen_record"),
        Index("ix_gen_record_plant_time", "plant_id", "recorded_at"),
        Index("ix_gen_record_inverter_time", "inverter_id", "recorded_at"),
    )


# ── Telemetry Alarm ───────────────────────────────────────────────────────────
class TelemetryAlarm(Base, TenantMixin, TimestampMixin):
    __tablename__ = "telemetry_alarm"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inverter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inverter_device.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    alarm_code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default=AlarmSeverity.WARNING)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=AlarmStatus.ACTIVE)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_alarm_plant_time", "plant_id", "occurred_at"),
        Index("ix_alarm_status", "organization_id", "status"),
    )


# ── Outage ────────────────────────────────────────────────────────────────────
class Outage(Base, TenantMixin, TimestampMixin):
    __tablename__ = "outage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    outage_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outage_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_loss_kwh: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    cause: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index("ix_outage_plant_time", "plant_id", "outage_start"),
    )
