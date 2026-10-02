"""
Phase 6 Acceptance Tests:
1. Declarative Rules DSL deterministic evaluation: identical inputs yield identical explainability trees.
2. Bitemporal time-travel: queries correctly evaluate effective rules across boundary dates.
3. Dry-run rule cohort testing: tests impact on multiple projects without state mutation.
"""
import uuid
from datetime import date
import pytest

from app.modules.regulations.service import regulations_service
from app.modules.regulations.models import AuthorityLevel, Regulation, RuleType, RuleStatus


def test_dsl_deterministic_evaluation():
    """
    Acceptance: Identical inputs MUST yield identical results every time.
    """
    condition = {
        "and": [
            {"field": "capacity_kw", "op": "<=", "value": 500},
            {"field": "state_code", "op": "==", "value": "MH"},
            {"field": "discom", "op": "in", "value": ["MSEDCL", "TATA_POWER_MUMBAI"]},
        ]
    }
    context_a = {"capacity_kw": 450, "state_code": "MH", "discom": "MSEDCL"}
    context_b = {"capacity_kw": 550, "state_code": "MH", "discom": "MSEDCL"}

    res1, reason1 = regulations_service.evaluate_condition(condition, context_a)
    res2, reason2 = regulations_service.evaluate_condition(condition, context_a)
    assert res1 is True
    assert res2 is True
    assert reason1 == reason2

    res_fail1, reason_fail1 = regulations_service.evaluate_condition(condition, context_b)
    res_fail2, reason_fail2 = regulations_service.evaluate_condition(condition, context_b)
    assert res_fail1 is False
    assert res_fail2 is False
    assert reason_fail1 == reason_fail2


def test_bitemporal_time_travel_boundary_lookups():
    """
    Acceptance: Time-travel queries correct at boundaries.
    Regulation effective from 2026-04-01 to 2028-03-31.
    """
    reg = Regulation(
        organization_id=uuid.uuid4(),
        authority_id=uuid.uuid4(),
        code="MERC-NET-METER-2026",
        title="MERC Net Metering Regulations 2026",
        effective_from=date(2026, 4, 1),
        effective_until=date(2028, 3, 31),
        is_active=True,
    )

    # 1. Day before effective date -> NOT effective
    assert regulations_service.is_regulation_effective_at(reg, date(2026, 3, 31)) is False

    # 2. Exact start boundary -> EFFECTIVE
    assert regulations_service.is_regulation_effective_at(reg, date(2026, 4, 1)) is True

    # 3. Mid-period -> EFFECTIVE
    assert regulations_service.is_regulation_effective_at(reg, date(2027, 1, 15)) is True

    # 4. Exact end boundary -> EFFECTIVE
    assert regulations_service.is_regulation_effective_at(reg, date(2028, 3, 31)) is True

    # 5. Day after expiration -> NOT effective
    assert regulations_service.is_regulation_effective_at(reg, date(2028, 4, 1)) is False


def test_dry_run_rule_cohort_evaluation():
    """
    Acceptance: Rule author can preview impact across a fleet of projects without mutating state.
    """
    condition = {
        "and": [
            {"field": "has_almm_modules", "op": "==", "value": True},
            {"field": "inverter_iec_tested", "op": "==", "value": True},
        ]
    }

    cohort = [
        {"project_id": "P1", "has_almm_modules": True, "inverter_iec_tested": True},
        {"project_id": "P2", "has_almm_modules": False, "inverter_iec_tested": True},
        {"project_id": "P3", "has_almm_modules": True, "inverter_iec_tested": False},
        {"project_id": "P4", "has_almm_modules": True, "inverter_iec_tested": True},
    ]

    results = regulations_service.dry_run_rule(condition, cohort)
    assert len(results) == 4
    passes = [r[0] for r in results]
    assert passes == [True, False, False, True]
