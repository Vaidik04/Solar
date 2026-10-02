import uuid
from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from app.modules.project.engine import workflow_engine
from app.modules.project.models import DiscomAppStatus, ProjectStage, ProjectStatus
from app.modules.project.public import ApplicationCreate, ProjectCreate, ProjectTransition
from app.modules.project.events import ProjectCreated, ProjectStageTransitioned


def test_valid_sequential_stage_transition():
    # Lead -> Site Survey: allowed
    res = workflow_engine.can_transition(ProjectStage.LEAD, ProjectStage.SITE_SURVEY)
    assert res.allowed is True
    assert len(res.reasons) == 0

    # Site Survey -> Engineering Design (with survey completed): allowed
    res2 = workflow_engine.can_transition(
        ProjectStage.SITE_SURVEY, ProjectStage.ENGINEERING_DESIGN, context={"survey_completed": True}
    )
    assert res2.allowed is True


def test_invalid_arbitrary_jump_transition():
    # Direct jump: Lead -> Commissioning (invalid DAG transition)
    res = workflow_engine.can_transition(ProjectStage.LEAD, ProjectStage.COMMISSIONING)
    assert res.allowed is False
    assert any("not permitted by workflow DAG" in r for r in res.reasons)


def test_discom_application_guard():
    # Proposal Accepted -> Discom Application requires consumer_number
    res_blocked = workflow_engine.can_transition(
        ProjectStage.PROPOSAL_ACCEPTED, ProjectStage.DISCOM_APPLICATION, context={"consumer_number": None}
    )
    assert res_blocked.allowed is False
    assert any("consumer number is required" in r for r in res_blocked.reasons)

    res_allowed = workflow_engine.can_transition(
        ProjectStage.PROPOSAL_ACCEPTED, ProjectStage.DISCOM_APPLICATION, context={"consumer_number": "MSEDCL_12345"}
    )
    assert res_allowed.allowed is True


def test_installation_guard():
    # -> Installation requires finalized BOM
    res_blocked = workflow_engine.can_transition(
        ProjectStage.PROCUREMENT, ProjectStage.INSTALLATION, context={"bom_finalized": False}
    )
    assert res_blocked.allowed is False
    assert any("Bill of Materials (BOM) must be finalized" in r for r in res_blocked.reasons)

    res_allowed = workflow_engine.can_transition(
        ProjectStage.PROCUREMENT, ProjectStage.INSTALLATION, context={"bom_finalized": True}
    )
    assert res_allowed.allowed is True


def test_commissioning_guard():
    # -> Commissioning requires approved WCR
    res_blocked = workflow_engine.can_transition(
        ProjectStage.WCR_GENERATION, ProjectStage.COMMISSIONING, context={"wcr_approved": False}
    )
    assert res_blocked.allowed is False
    assert any("Work Completion Report (WCR) is required" in r for r in res_blocked.reasons)

    res_allowed = workflow_engine.can_transition(
        ProjectStage.WCR_GENERATION, ProjectStage.COMMISSIONING, context={"wcr_approved": True}
    )
    assert res_allowed.allowed is True


def test_sla_duration_calculation():
    now = datetime.now(timezone.utc)
    # Stage entered 10 hours ago; SLA for LEAD is 48 hours -> not breached
    entered_at = now - timedelta(hours=10)
    dur, hours, breached = workflow_engine.calculate_stage_duration_and_sla(ProjectStage.LEAD, entered_at, now)
    assert dur == 36000
    assert hours == 10.0
    assert breached is False

    # Stage entered 72 hours ago; SLA for LEAD (48h) -> breached!
    entered_at_breached = now - timedelta(hours=72)
    dur2, hours2, breached2 = workflow_engine.calculate_stage_duration_and_sla(
        ProjectStage.LEAD, entered_at_breached, now
    )
    assert hours2 == 72.0
    assert breached2 is True


def test_project_domain_events():
    org_id = uuid.uuid4()
    proj_id = uuid.uuid4()

    event = ProjectCreated(
        organization_id=org_id,
        project_id=proj_id,
        plant_id="SOL-MH-000001",
        customer_id=uuid.uuid4(),
        site_id=uuid.uuid4(),
        capacity_kw_dc=15.0,
        capacity_kw_ac=12.0,
    )
    payload = event.to_dict()
    assert payload["plant_id"] == "SOL-MH-000001"
    assert payload["capacity_kw_dc"] == 15.0
    assert event.event_type == "ProjectCreated"

    trans_event = ProjectStageTransitioned(
        organization_id=org_id,
        project_id=proj_id,
        plant_id="SOL-MH-000001",
        from_stage=ProjectStage.LEAD,
        to_stage=ProjectStage.SITE_SURVEY,
        actor_user_id=uuid.uuid4(),
        is_override=False,
    )
    assert trans_event.event_type == "ProjectStageTransitioned"
    assert trans_event.to_stage == "site_survey"
