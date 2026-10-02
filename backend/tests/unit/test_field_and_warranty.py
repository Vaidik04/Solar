"""
Unit tests for Field Operations and Warranty Module
"""
import uuid
from datetime import date
import pytest

from app.modules.field.models import (
    CommissioningStatus,
    InspectionStatus,
    MeterType,
    WCRStatus,
)
from app.modules.field.public import (
    CommissioningCreate,
    InspectionCreate,
    InspectionItemCreate,
    InspectionSubmit,
    InspectionTemplateCreate,
    MeterCreate,
    WCRCreate,
)
from app.modules.warranty.models import ClaimStatus, WarrantyType
from app.modules.warranty.public import (
    WarrantyClaimCreate,
    WarrantyClaimStatusUpdate,
    WarrantyCreate,
)


def test_meter_create_valid():
    meter = MeterCreate(
        project_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        meter_type=MeterType.NET_METER,
        make="Secure Meters",
        model="Premier 300",
        serial_number="SEC-2026-99981",
        capacity_kw=50.0,
    )
    assert meter.serial_number == "SEC-2026-99981"
    assert meter.capacity_kw == 50.0


def test_inspection_template_and_scoring():
    template = InspectionTemplateCreate(
        code="INSP-PRE-COMM",
        name="Pre-Commissioning Quality Audit",
        checklist=[
            {"code": "EARTHING", "label": "Earth resistance <= 5 ohms"},
            {"code": "INVERTER_MOUNT", "label": "Inverter mounted with proper clearance"},
            {"code": "CABLE_DRESSING", "label": "DC cables UV protected & dressed"},
            {"code": "ISOLATOR", "label": "DC isolator switch functional"},
            {"code": "WARNING_LABELS", "label": "Danger / warning labels affixed"},
        ],
    )
    assert len(template.checklist) == 5

    # 4 out of 5 pass -> 80% -> pass
    items_pass = [
        InspectionItemCreate(check_code="EARTHING", label="Earth", result="pass"),
        InspectionItemCreate(check_code="INVERTER_MOUNT", label="Mount", result="pass"),
        InspectionItemCreate(check_code="CABLE_DRESSING", label="Cables", result="pass"),
        InspectionItemCreate(check_code="ISOLATOR", label="Isolator", result="pass"),
        InspectionItemCreate(check_code="WARNING_LABELS", label="Labels", result="fail"),
    ]
    pass_count = sum(1 for i in items_pass if i.result == "pass")
    score_pass = pass_count / len(items_pass) * 100.0
    assert score_pass == 80.0
    assert (score_pass >= 80.0) is True

    # 3 out of 5 pass -> 60% -> fail
    items_fail = items_pass[:3] + [
        InspectionItemCreate(check_code="ISOLATOR", label="Isolator", result="fail"),
        InspectionItemCreate(check_code="WARNING_LABELS", label="Labels", result="fail"),
    ]
    pass_count_fail = sum(1 for i in items_fail if i.result == "pass")
    score_fail = pass_count_fail / len(items_fail) * 100.0
    assert score_fail == 60.0
    assert (score_fail >= 80.0) is False


def test_wcr_and_commissioning_dtos():
    proj_id = uuid.uuid4()
    wcr = WCRCreate(
        project_id=proj_id,
        plant_id="PLANT-MH-001",
        capacity_installed_kw=45.5,
        asset_ids=[str(uuid.uuid4()) for _ in range(3)],
        completion_date=date(2026, 3, 15),
    )
    assert wcr.capacity_installed_kw == 45.5
    assert len(wcr.asset_ids) == 3

    comm = CommissioningCreate(
        project_id=proj_id,
        plant_id="PLANT-MH-001",
        commissioned_date=date(2026, 3, 16),
        initial_generation_kwh=120.5,
        discom_approval_reference="MSEDCL/COMM/2026/0892",
    )
    assert comm.initial_generation_kwh == 120.5


def test_warranty_and_claim_lifecycle_dtos():
    warranty = WarrantyCreate(
        project_id=uuid.uuid4(),
        plant_id="PLANT-MH-001",
        warranty_type=WarrantyType.MODULE_PERFORMANCE,
        provider_name="Tier-1 Solar Co.",
        start_date=date(2026, 1, 1),
        end_date=date(2051, 1, 1),
        period_years=25,
        coverage_details="25-year linear performance warranty: >= 80% at year 25",
    )
    assert warranty.period_years == 25

    claim = WarrantyClaimCreate(
        warranty_id=uuid.uuid4(),
        defect_description="Delamination and hot spots observed on string 4",
        affected_components=["MOD-SN-0012", "MOD-SN-0013"],
    )
    assert len(claim.affected_components) == 2

    status_update = WarrantyClaimStatusUpdate(
        status=ClaimStatus.RESOLVED_ACCEPTED,
        notes="Manufacturer inspected and agreed to replace 2 modules under warranty.",
        replacement_asset_ids=[str(uuid.uuid4()) for _ in range(2)],
    )
    assert status_update.status == "resolved_accepted"
    assert len(status_update.replacement_asset_ids) == 2
