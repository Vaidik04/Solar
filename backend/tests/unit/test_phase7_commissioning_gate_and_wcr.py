"""
Phase 7 Acceptance Tests:
1. Commissioning Readiness Gate: blocks commissioning with explicit explainable blockers.
2. Draft vs Final WCR: WCR signing freezes report, generates cryptographic SHA-256 seal and QR verification token.
3. Successful commissioning gate clearance when all requirements are met.
"""
import uuid
import hashlib
from datetime import date, datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.field.service import FieldService
from app.modules.field.models import (
    CommissioningRecord,
    CommissioningStatus,
    Inspection,
    InspectionStatus,
    Meter,
    MeterType,
    WCR,
    WCRStatus,
)


@pytest.mark.asyncio
async def test_commissioning_blocked_with_explainable_blockers():
    """
    Acceptance: Commissioning blocked with explainable blockers when prerequisites are unfulfilled.
    """
    service = FieldService()
    session = AsyncMock()
    org_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Empty DB state -> No meter, No WCR, No inspection
    mock_meters_result = MagicMock()
    mock_meters_result.scalars.return_value.all.return_value = []

    mock_wcrs_result = MagicMock()
    mock_wcrs_result.scalars.return_value.all.return_value = []

    mock_insps_result = MagicMock()
    mock_insps_result.scalars.return_value.all.return_value = []

    session.execute.side_effect = [
        mock_meters_result,
        mock_wcrs_result,
        mock_insps_result,
    ]

    gate_result = await service.evaluate_commissioning_readiness(session, org_id, project_id)

    assert gate_result["is_ready"] is False
    assert gate_result["status"] == "BLOCKED"
    assert len(gate_result["blockers"]) == 3
    assert any("meter" in b.lower() for b in gate_result["blockers"])
    assert any("wcr" in b.lower() for b in gate_result["blockers"])
    assert any("inspection" in b.lower() for b in gate_result["blockers"])


@pytest.mark.asyncio
async def test_draft_vs_final_wcr_approval_and_signing():
    """
    Acceptance: Draft WCR converts to Final APPROVED status and receives cryptographic HMAC QR seal.
    """
    service = FieldService()
    session = AsyncMock()
    org_id = uuid.uuid4()
    wcr_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    draft_wcr = WCR(
        id=wcr_id,
        organization_id=org_id,
        project_id=uuid.uuid4(),
        plant_id="SOL-MH-000042",
        wcr_number="WCR-SOL-MH-000042-V1",
        wcr_version=1,
        status=WCRStatus.SUBMITTED,
        capacity_installed_kw=500.0,
        document_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )

    mock_get = MagicMock()
    mock_get.scalar_one_or_none.return_value = draft_wcr
    session.execute.return_value = mock_get

    approved_wcr = await service.approve_and_sign_wcr(
        session, org_id, wcr_id, actor_id, signing_key="secure-test-signing-key"
    )

    assert approved_wcr.status == WCRStatus.APPROVED
    assert approved_wcr.approved_by_user_id == actor_id
    assert approved_wcr.qr_verification_token is not None
    assert len(approved_wcr.qr_verification_token) == 64  # SHA-256 hex string


@pytest.mark.asyncio
async def test_commissioning_gate_cleared_when_prerequisites_met():
    """
    Acceptance: Commissioning approved when Meter, Approved WCR, and Passed Inspections exist.
    """
    service = FieldService()
    session = AsyncMock()
    org_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # 1. Registered meter
    mock_meter = Meter(
        organization_id=org_id,
        project_id=project_id,
        plant_id="SOL-MH-000042",
        meter_type=MeterType.NET_METER,
        serial_number="MTR-998822",
    )
    mock_meters_result = MagicMock()
    mock_meters_result.scalars.return_value.all.return_value = [mock_meter]

    # 2. Approved WCR
    mock_wcr = WCR(
        organization_id=org_id,
        project_id=project_id,
        plant_id="SOL-MH-000042",
        wcr_number="WCR-SOL-MH-000042-V1",
        status=WCRStatus.APPROVED,
    )
    mock_wcrs_result = MagicMock()
    mock_wcrs_result.scalars.return_value.all.return_value = [mock_wcr]

    # 3. Passed inspection
    mock_insp = Inspection(
        organization_id=org_id,
        project_id=project_id,
        status=InspectionStatus.COMPLETED,
    )
    mock_insps_result = MagicMock()
    mock_insps_result.scalars.return_value.all.return_value = [mock_insp]

    session.execute.side_effect = [
        mock_meters_result,
        mock_wcrs_result,
        mock_insps_result,
    ]

    gate_result = await service.evaluate_commissioning_readiness(session, org_id, project_id)

    assert gate_result["is_ready"] is True
    assert gate_result["status"] == "APPROVED_FOR_COMMISSIONING"
    assert len(gate_result["blockers"]) == 0
    assert len(gate_result["checks_passed"]) == 3
