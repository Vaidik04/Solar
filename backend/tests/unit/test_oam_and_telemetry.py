"""
Unit tests for O&M and Telemetry Monitoring Modules
"""
import uuid
from datetime import date, datetime, timezone
import pytest

from app.modules.oam.models import (
    TaskFrequency,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    VisitStatus,
)
from app.modules.oam.public import (
    MaintenancePlanCreate,
    MaintenanceTaskCreate,
    SLAPolicyCreate,
    TicketCreate,
    TicketUpdate,
    VisitCreate,
    VisitUpdate,
)
from app.modules.telemetry_data.models import (
    AlarmSeverity,
    AlarmStatus,
    DataSourceProtocol,
)
from app.modules.telemetry_data.public import (
    DataSourceConfigCreate,
    GenerationRecordCreate,
    GenerationSummaryOut,
    InverterCreate,
    OutageCreate,
    TelemetryAlarmCreate,
)


def test_oam_sla_policy_and_tickets():
    policy = SLAPolicyCreate(
        name="Critical Inverter Breakdown SLA",
        priority=TicketPriority.CRITICAL,
        first_response_hours=2,
        resolution_hours=12,
        escalation_hours=4,
    )
    assert policy.first_response_hours == 2
    assert policy.resolution_hours == 12

    ticket = TicketCreate(
        project_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        title="Inverter 2 Grid Fault - 0kW Output",
        description="Inverter stopped feeding power since 11:30 AM due to grid overvoltage trip.",
        category=TicketCategory.EMERGENCY,
        priority=TicketPriority.CRITICAL,
    )
    assert ticket.priority == "critical"
    assert ticket.category == "emergency"

    ticket_update = TicketUpdate(
        status=TicketStatus.IN_PROGRESS,
        notes="Technician dispatched with replacement fuses and multimeter.",
    )
    assert ticket_update.status == "in_progress"


def test_maintenance_plan_and_visit():
    plan = MaintenancePlanCreate(
        project_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        name="Annual Solar Plant Preventive Maintenance",
        start_date=date(2026, 1, 1),
        tasks=[
            MaintenanceTaskCreate(
                title="Bi-weekly Module Cleaning & Visual Inspection",
                frequency=TaskFrequency.WEEKLY,
                estimated_duration_hours=4.0,
            ),
            MaintenanceTaskCreate(
                title="Quarterly Inverter Heat Sink & Fan Cleaning",
                frequency=TaskFrequency.QUARTERLY,
                estimated_duration_hours=2.0,
            ),
        ],
    )
    assert len(plan.tasks) == 2
    assert plan.tasks[0].frequency == "weekly"

    visit = VisitCreate(
        project_id=uuid.uuid4(),
        technician_user_id=uuid.uuid4(),
        planned_date=date(2026, 3, 20),
    )
    assert visit.planned_date == date(2026, 3, 20)


def test_telemetry_inverter_and_data_source():
    inv = InverterCreate(
        project_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        make="Sungrow",
        model="SG50CX",
        serial_number="SG-2026-00451",
        rated_capacity_kw=50.0,
        device_specs={"mppt_count": 5, "strings_per_mppt": 2},
        data_source=DataSourceConfigCreate(
            protocol=DataSourceProtocol.MODBUS_TCP,
            host="192.168.1.150",
            port=502,
            unit_id=1,
            poll_interval_seconds=60,
        ),
    )
    assert inv.rated_capacity_kw == 50.0
    assert inv.data_source.protocol == "modbus_tcp"
    assert inv.data_source.port == 502


def test_generation_record_and_alarm():
    rec = GenerationRecordCreate(
        inverter_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        recorded_at=datetime.now(timezone.utc),
        interval_minutes=15,
        energy_kwh=12.45,
        peak_power_kw=50.2,
        avg_power_kw=49.8,
        grid_voltage_v=415.2,
        grid_frequency_hz=50.02,
    )
    assert rec.energy_kwh == 12.45
    assert rec.grid_frequency_hz == 50.02

    summary = GenerationSummaryOut(
        plant_id="PLANT-MH-001",
        total_energy_kwh=2450.8,
        peak_power_kw=52.1,
        avg_power_kw=38.4,
        records_count=96,
    )
    assert summary.records_count == 96
    assert summary.total_energy_kwh == 2450.8

    alarm = TelemetryAlarmCreate(
        inverter_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        alarm_code="ALM_GRID_OVERVOLTAGE",
        severity=AlarmSeverity.ERROR,
        description="Grid voltage exceeded 440V threshold for 30 seconds",
        occurred_at=datetime.now(timezone.utc),
    )
    assert alarm.alarm_code == "ALM_GRID_OVERVOLTAGE"
    assert alarm.severity == "error"

    outage = OutageCreate(
        plant_id="PLANT-MH-001",
        project_id=uuid.uuid4(),
        outage_start=datetime.now(timezone.utc),
        cause="DISCOM planned feeder shutdown for maintenance",
        estimated_loss_kwh=150.0,
    )
    assert outage.estimated_loss_kwh == 150.0
