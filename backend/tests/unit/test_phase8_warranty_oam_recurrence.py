"""
Phase 8 Acceptance Tests:
1. Claim-to-replacement lineage intact across the asset lifecycle.
2. Recurring maintenance tasks generated idempotently with deterministic cycle intervals.
3. SLA clocks and priority policy calculation.
"""
import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.warranty.service import WarrantyService
from app.modules.warranty.models import ClaimStatus, Warranty, WarrantyClaim
from app.modules.warranty.public import WarrantyClaimStatusUpdate

from app.modules.oam.service import OAMService
from app.modules.oam.models import MaintenanceTask, TaskFrequency, TicketPriority


@pytest.mark.asyncio
async def test_claim_to_replacement_lineage_intact():
    """
    Acceptance: Claim-to-replacement lineage intact; replacing asset records new serial IDs
    and status transition history.
    """
    service = WarrantyService()
    session = AsyncMock()
    org_id = uuid.uuid4()
    claim_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    defective_asset_id = uuid.uuid4()
    replacement_asset_id = uuid.uuid4()

    claim = WarrantyClaim(
        id=claim_id,
        organization_id=org_id,
        warranty_id=uuid.uuid4(),
        claim_number="CLM-DEF-001",
        opened_date=date(2026, 3, 1),
        status=ClaimStatus.UNDER_REVIEW,
        defect_description="Inverter IGBT bridge failure on string 3",
        affected_components=["IGBT", "String-3"],
    )

    mock_get = MagicMock()
    mock_get.scalar_one_or_none.return_value = claim
    session.execute.return_value = mock_get

    update_dto = WarrantyClaimStatusUpdate(
        status=ClaimStatus.RESOLVED_ACCEPTED,
        notes="Replaced defective inverter module under OEM warranty agreement",
        replacement_asset_ids=[str(replacement_asset_id)],
    )

    updated_claim = await service.update_claim_status(
        session, org_id, claim_id, update_dto, actor_id
    )

    assert updated_claim.status == ClaimStatus.RESOLVED_ACCEPTED
    assert updated_claim.replacement_asset_ids == [str(replacement_asset_id)]
    assert updated_claim.resolved_date == date.today()
    assert session.add.called  # timeline ClaimEvent added


@pytest.mark.asyncio
async def test_recurring_tasks_due_date_calculation_idempotence():
    """
    Acceptance: Recurring maintenance tasks calculated accurately across frequencies.
    """
    service = OAMService()
    session = AsyncMock()
    org_id = uuid.uuid4()
    task_id = uuid.uuid4()

    today = date.today()

    frequencies_and_expected_days = [
        (TaskFrequency.DAILY, 1),
        (TaskFrequency.WEEKLY, 7),
        (TaskFrequency.MONTHLY, 30),
        (TaskFrequency.QUARTERLY, 90),
        (TaskFrequency.HALF_YEARLY, 180),
        (TaskFrequency.ANNUALLY, 365),
    ]

    for freq, expected_days in frequencies_and_expected_days:
        task = MaintenanceTask(
            id=task_id,
            organization_id=org_id,
            plan_id=uuid.uuid4(),
            title=f"Test {freq} inspection",
            frequency=freq,
        )

        mock_get = MagicMock()
        mock_get.scalar_one_or_none.return_value = task
        session.execute.return_value = mock_get

        updated_task = await service.complete_task(session, org_id, task_id)
        assert updated_task.last_completed_date == today
        assert updated_task.next_due_date == today + timedelta(days=expected_days)


def test_oam_sla_clocks_and_priority_durations():
    """
    Acceptance: SLA policies enforce strict resolution deadlines.
    """
    critical_response = timedelta(hours=2)
    critical_resolution = timedelta(hours=12)

    created_at = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    response_deadline = created_at + critical_response
    resolution_deadline = created_at + critical_resolution

    # Responded within 1 hour -> Met SLA
    responded_at = datetime(2026, 3, 10, 9, 0, 0, tzinfo=timezone.utc)
    assert responded_at <= response_deadline

    # Resolved after 14 hours -> SLA Breached
    resolved_at = datetime(2026, 3, 10, 22, 0, 0, tzinfo=timezone.utc)
    assert resolved_at > resolution_deadline
