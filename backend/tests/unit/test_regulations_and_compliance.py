"""
Unit tests for Regulations DSL Engine and Compliance Module
"""
import uuid
import pytest
from datetime import datetime, timezone

from app.modules.regulations.service import regulations_service
from app.modules.regulations.public import (
    AuthorityCreate,
    RegulationCreate,
    RuleCreate,
    RuleSetCreate,
)
from app.modules.regulations.models import AuthorityLevel, RuleType, RuleStatus
from app.modules.compliance.public import (
    ComplianceRunTrigger,
    ComplianceWaiverCreate,
)
from app.modules.compliance.models import ResultStatus, RunStatus


def test_dsl_simple_comparisons():
    ctx = {"capacity_kw": 100, "state_code": "MH", "system_type": "grid_tied"}

    # ==
    passed, msg = regulations_service.evaluate_condition(
        {"field": "state_code", "op": "==", "value": "MH"}, ctx
    )
    assert passed is True

    # !=
    passed, _ = regulations_service.evaluate_condition(
        {"field": "state_code", "op": "!=", "value": "GJ"}, ctx
    )
    assert passed is True

    # <=
    passed, _ = regulations_service.evaluate_condition(
        {"field": "capacity_kw", "op": "<=", "value": 100}, ctx
    )
    assert passed is True

    # >
    passed, _ = regulations_service.evaluate_condition(
        {"field": "capacity_kw", "op": ">", "value": 100}, ctx
    )
    assert passed is False

    # <
    passed, _ = regulations_service.evaluate_condition(
        {"field": "capacity_kw", "op": "<", "value": 150}, ctx
    )
    assert passed is True


def test_dsl_collections_and_membership():
    ctx = {
        "discom": "MSEDCL",
        "documents": ["aadhaar", "electricity_bill", "sanction_letter"],
    }

    # in
    passed, _ = regulations_service.evaluate_condition(
        {"field": "discom", "op": "in", "value": ["MSEDCL", "BESCOM", "TSSPDCL"]}, ctx
    )
    assert passed is True

    # not_in
    passed, _ = regulations_service.evaluate_condition(
        {"field": "discom", "op": "not_in", "value": ["UGVCL", "DGVCL"]}, ctx
    )
    assert passed is True

    # contains (collection contains element)
    passed, _ = regulations_service.evaluate_condition(
        {"field": "documents", "op": "contains", "value": "sanction_letter"}, ctx
    )
    assert passed is True

    # contains missing element
    passed, _ = regulations_service.evaluate_condition(
        {"field": "documents", "op": "contains", "value": "noc_fire"}, ctx
    )
    assert passed is False


def test_dsl_nested_boolean_logic():
    ctx = {
        "capacity_kw": 25,
        "state_code": "KA",
        "system_type": "rooftop",
        "documents": ["pan", "electricity_bill"],
    }

    # AND pass
    and_cond = {
        "and": [
            {"field": "capacity_kw", "op": "<=", "value": 50},
            {"field": "state_code", "op": "==", "value": "KA"},
            {"field": "documents", "op": "contains", "value": "pan"},
        ]
    }
    passed, _ = regulations_service.evaluate_condition(and_cond, ctx)
    assert passed is True

    # AND fail
    and_fail = {
        "and": [
            {"field": "capacity_kw", "op": "<=", "value": 10},  # Fails: 25 > 10
            {"field": "state_code", "op": "==", "value": "KA"},
        ]
    }
    passed, msg = regulations_service.evaluate_condition(and_fail, ctx)
    assert passed is False
    assert "Subcondition failed" in msg

    # OR pass
    or_cond = {
        "or": [
            {"field": "state_code", "op": "==", "value": "DL"},  # False
            {"field": "state_code", "op": "==", "value": "KA"},  # True
        ]
    }
    passed, _ = regulations_service.evaluate_condition(or_cond, ctx)
    assert passed is True

    # NOT pass
    not_cond = {
        "not": {"field": "state_code", "op": "==", "value": "MH"}  # Inner is False -> NOT is True
    }
    passed, _ = regulations_service.evaluate_condition(not_cond, ctx)
    assert passed is True


def test_regulations_and_compliance_dtos():
    auth = AuthorityCreate(
        code="MERC",
        name="Maharashtra Electricity Regulatory Commission",
        level=AuthorityLevel.STATE,
        state_code="MH",
    )
    assert auth.code == "MERC"

    reg = RegulationCreate(
        authority_id=uuid.uuid4(),
        code="MERC-RPO-2026",
        title="Rooftop Net Metering Regulations 2026",
        applies_to_states=["MH"],
    )
    assert reg.code == "MERC-RPO-2026"

    rule = RuleCreate(
        regulation_id=uuid.uuid4(),
        code="MERC-CAP-LIMIT",
        title="Rooftop Capacity Limit 1000kW",
        rule_type=RuleType.CAPACITY_LIMIT,
        condition_dsl={"field": "capacity_kw", "op": "<=", "value": 1000},
        min_capacity_kw="1",
        max_capacity_kw="1000",
    )
    assert rule.max_capacity_kw == "1000"

    ruleset = RuleSetCreate(
        code="MH-RESIDENTIAL-NET-METER",
        name="Maharashtra Residential Net Metering Rules",
        state_code="MH",
        rule_ids=[str(uuid.uuid4())],
    )
    assert len(ruleset.rule_ids) == 1

    trigger = ComplianceRunTrigger(
        project_id=uuid.uuid4(),
        context_override={"capacity_kw": 750, "state_code": "MH"},
    )
    assert trigger.context_override["capacity_kw"] == 750

    waiver = ComplianceWaiverCreate(
        project_id=uuid.uuid4(),
        rule_code="MERC-CAP-LIMIT",
        reason="Approved by DISCOM CEIG special exemption",
    )
    assert waiver.rule_code == "MERC-CAP-LIMIT"
