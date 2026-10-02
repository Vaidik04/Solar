"""
Solar Operations OS — Regulations Service
Handles Authorities, Regulations, Rules, RuleSets, and Rule DSL evaluation.
"""
from __future__ import annotations

import operator
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.modules.regulations.events import RegulationCreated, RuleCreated, RuleSetCreated
from app.modules.regulations.models import Authority, Regulation, Rule, RuleSet
from app.modules.regulations.public import (
    AuthorityCreate,
    RegulationCreate,
    RegulationUpdate,
    RuleCreate,
    RuleEvaluationResult,
    RuleSetCreate,
    RuleSetUpdate,
    RuleUpdate,
)


class RegulationsService:
    # ── DSL Evaluation Engine ──────────────────────────────────────────────────
    def evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> tuple[bool, str]:
        """
        Evaluates a declarative rule condition DSL against a project/site context dictionary.

        Supported DSL constructs:
        - {"field": "capacity_kw", "op": "<=", "value": 500}
        - {"field": "state_code", "op": "==", "value": "MH"}
        - {"field": "documents", "op": "contains", "value": "sanction_letter"}
        - {"and": [ {...}, {...} ]}
        - {"or": [ {...}, {...} ]}
        - {"not": {...}}
        """
        if not condition:
            return True, "No conditions specified (default pass)"

        if "and" in condition:
            for sub in condition["and"]:
                passed, reason = self.evaluate_condition(sub, context)
                if not passed:
                    return False, f"Subcondition failed: {reason}"
            return True, "All AND conditions met"

        if "or" in condition:
            reasons = []
            for sub in condition["or"]:
                passed, reason = self.evaluate_condition(sub, context)
                if passed:
                    return True, f"OR condition met: {reason}"
                reasons.append(reason)
            return False, f"None of OR conditions met: {'; '.join(reasons)}"

        if "not" in condition:
            passed, reason = self.evaluate_condition(condition["not"], context)
            if passed:
                return False, f"NOT condition failed (inner passed: {reason})"
            return True, "NOT condition passed"

        field = condition.get("field")
        op = condition.get("op", "==")
        expected = condition.get("value")

        if not field:
            return True, "No field specified"

        actual = context.get(field)

        try:
            if op == "==":
                matched = actual == expected
            elif op == "!=":
                matched = actual != expected
            elif op == ">":
                matched = float(actual) > float(expected)
            elif op == ">=":
                matched = float(actual) >= float(expected)
            elif op == "<":
                matched = float(actual) < float(expected)
            elif op == "<=":
                matched = float(actual) <= float(expected)
            elif op == "in":
                matched = actual in expected if isinstance(expected, (list, set, tuple)) else False
            elif op == "not_in":
                matched = actual not in expected if isinstance(expected, (list, set, tuple)) else True
            elif op == "contains":
                matched = expected in actual if isinstance(actual, (list, set, tuple, str)) else False
            elif op == "exists":
                matched = (actual is not None) == bool(expected)
            else:
                return False, f"Unsupported operator '{op}'"

            if matched:
                return True, f"Condition passed: {field} ({actual}) {op} {expected}"
            else:
                return False, f"Condition failed: {field} ({actual}) does not satisfy {op} {expected}"

        except (ValueError, TypeError) as e:
            return False, f"Error evaluating {field} with {op}: {str(e)}"

    async def evaluate_rule(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        rule_id: uuid.UUID,
        context: Dict[str, Any],
    ) -> RuleEvaluationResult:
        rule = await self.get_rule(session, org_id, rule_id)

        # Check capacity range if defined on rule
        cap = context.get("capacity_kw")
        if cap is not None and rule.min_capacity_kw:
            try:
                if float(cap) < float(rule.min_capacity_kw):
                    return RuleEvaluationResult(
                        rule_id=rule.id,
                        rule_code=rule.code,
                        passed=False,
                        reason=f"Capacity {cap} kW below rule minimum {rule.min_capacity_kw} kW",
                        details={"context": context},
                    )
            except ValueError:
                pass

        if cap is not None and rule.max_capacity_kw:
            try:
                if float(cap) > float(rule.max_capacity_kw):
                    return RuleEvaluationResult(
                        rule_id=rule.id,
                        rule_code=rule.code,
                        passed=False,
                        reason=f"Capacity {cap} kW exceeds rule maximum {rule.max_capacity_kw} kW",
                        details={"context": context},
                    )
            except ValueError:
                pass

        # Check system type if defined on rule
        sys_type = context.get("system_type")
        if sys_type and rule.applies_to_system_types:
            if sys_type not in rule.applies_to_system_types:
                return RuleEvaluationResult(
                    rule_id=rule.id,
                    rule_code=rule.code,
                    passed=True,
                    reason=f"Rule not applicable to system type {sys_type}",
                    details={"skipped": True},
                )

        passed, reason = self.evaluate_condition(rule.condition_dsl, context)
        return RuleEvaluationResult(
            rule_id=rule.id,
            rule_code=rule.code,
            passed=passed,
            reason=reason,
            details={"condition_dsl": rule.condition_dsl, "context": context},
        )

    def is_regulation_effective_at(self, reg: Regulation, as_of_date: Any) -> bool:
        """
        Bitemporal time-travel check: determines whether regulation was legally in effect
        on a specific target date (boundary-inclusive).
        """
        if reg.effective_from and reg.effective_from > as_of_date:
            return False
        if reg.effective_until and reg.effective_until < as_of_date:
            return False
        return True

    def dry_run_rule(
        self, condition_dsl: Dict[str, Any], contexts: List[Dict[str, Any]]
    ) -> List[tuple[bool, str]]:
        """
        Evaluates a rule against a cohort of project contexts without committing changes.
        """
        return [self.evaluate_condition(condition_dsl, ctx) for ctx in contexts]

    # ── Authority Operations ──────────────────────────────────────────────────
    async def create_authority(
        self, session: AsyncSession, org_id: uuid.UUID, data: AuthorityCreate
    ) -> Authority:
        existing = (
            await session.execute(
                select(Authority).where(
                    Authority.organization_id == org_id, Authority.code == data.code
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Authority code '{data.code}' already exists")

        auth = Authority(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            level=data.level,
            state_code=data.state_code,
            website=data.website,
        )
        session.add(auth)
        return auth

    async def list_authorities(
        self, session: AsyncSession, org_id: uuid.UUID, level: Optional[str] = None
    ) -> List[Authority]:
        stmt = select(Authority).where(Authority.organization_id == org_id)
        if level:
            stmt = stmt.where(Authority.level == level)
        return list((await session.execute(stmt)).scalars().all())

    async def get_authority(
        self, session: AsyncSession, org_id: uuid.UUID, authority_id: uuid.UUID
    ) -> Authority:
        auth = (
            await session.execute(
                select(Authority).where(
                    Authority.organization_id == org_id, Authority.id == authority_id
                )
            )
        ).scalar_one_or_none()
        if not auth:
            raise NotFoundError(f"Authority {authority_id} not found")
        return auth

    # ── Regulation Operations ─────────────────────────────────────────────────
    async def create_regulation(
        self, session: AsyncSession, org_id: uuid.UUID, data: RegulationCreate
    ) -> Regulation:
        await self.get_authority(session, org_id, data.authority_id)

        existing = (
            await session.execute(
                select(Regulation).where(
                    Regulation.organization_id == org_id, Regulation.code == data.code
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Regulation code '{data.code}' already exists")

        reg = Regulation(
            organization_id=org_id,
            authority_id=data.authority_id,
            code=data.code,
            title=data.title,
            description=data.description,
            effective_from=data.effective_from,
            effective_until=data.effective_until,
            is_active=data.is_active,
            applies_to_states=data.applies_to_states,
        )
        session.add(reg)
        await event_bus.publish(
            RegulationCreated(
                organization_id=org_id,
                regulation_id=reg.id,
                code=reg.code,
                authority_id=reg.authority_id,
            )
        )
        return reg

    async def list_regulations(
        self, session: AsyncSession, org_id: uuid.UUID, authority_id: Optional[uuid.UUID] = None
    ) -> List[Regulation]:
        stmt = select(Regulation).where(Regulation.organization_id == org_id)
        if authority_id:
            stmt = stmt.where(Regulation.authority_id == authority_id)
        return list((await session.execute(stmt)).scalars().all())

    async def get_regulation(
        self, session: AsyncSession, org_id: uuid.UUID, regulation_id: uuid.UUID
    ) -> Regulation:
        reg = (
            await session.execute(
                select(Regulation).where(
                    Regulation.organization_id == org_id, Regulation.id == regulation_id
                )
            )
        ).scalar_one_or_none()
        if not reg:
            raise NotFoundError(f"Regulation {regulation_id} not found")
        return reg

    # ── Rule Operations ───────────────────────────────────────────────────────
    async def create_rule(
        self, session: AsyncSession, org_id: uuid.UUID, data: RuleCreate
    ) -> Rule:
        await self.get_regulation(session, org_id, data.regulation_id)

        existing = (
            await session.execute(
                select(Rule).where(
                    Rule.organization_id == org_id,
                    Rule.regulation_id == data.regulation_id,
                    Rule.code == data.code,
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Rule code '{data.code}' already exists in regulation")

        rule = Rule(
            organization_id=org_id,
            regulation_id=data.regulation_id,
            code=data.code,
            title=data.title,
            rule_type=data.rule_type,
            status=data.status,
            description=data.description,
            condition_dsl=data.condition_dsl,
            action_meta=data.action_meta,
            min_capacity_kw=data.min_capacity_kw,
            max_capacity_kw=data.max_capacity_kw,
            applies_to_system_types=data.applies_to_system_types,
        )
        session.add(rule)
        await event_bus.publish(
            RuleCreated(
                organization_id=org_id,
                regulation_id=rule.regulation_id,
                rule_id=rule.id,
                code=rule.code,
                rule_type=rule.rule_type,
            )
        )
        return rule

    async def list_rules(
        self, session: AsyncSession, org_id: uuid.UUID, regulation_id: Optional[uuid.UUID] = None
    ) -> List[Rule]:
        stmt = select(Rule).where(Rule.organization_id == org_id)
        if regulation_id:
            stmt = stmt.where(Rule.regulation_id == regulation_id)
        return list((await session.execute(stmt)).scalars().all())

    async def get_rule(
        self, session: AsyncSession, org_id: uuid.UUID, rule_id: uuid.UUID
    ) -> Rule:
        rule = (
            await session.execute(
                select(Rule).where(Rule.organization_id == org_id, Rule.id == rule_id)
            )
        ).scalar_one_or_none()
        if not rule:
            raise NotFoundError(f"Rule {rule_id} not found")
        return rule

    # ── RuleSet Operations ────────────────────────────────────────────────────
    async def create_ruleset(
        self, session: AsyncSession, org_id: uuid.UUID, data: RuleSetCreate
    ) -> RuleSet:
        existing = (
            await session.execute(
                select(RuleSet).where(
                    RuleSet.organization_id == org_id, RuleSet.code == data.code
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError(f"RuleSet code '{data.code}' already exists")

        ruleset = RuleSet(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            state_code=data.state_code,
            system_type=data.system_type,
            description=data.description,
            rule_ids=data.rule_ids,
        )
        session.add(ruleset)
        await event_bus.publish(
            RuleSetCreated(
                organization_id=org_id,
                rule_set_id=ruleset.id,
                code=ruleset.code,
                state_code=ruleset.state_code,
            )
        )
        return ruleset

    async def list_rulesets(
        self, session: AsyncSession, org_id: uuid.UUID, state_code: Optional[str] = None
    ) -> List[RuleSet]:
        stmt = select(RuleSet).where(RuleSet.organization_id == org_id)
        if state_code:
            stmt = stmt.where(RuleSet.state_code == state_code)
        return list((await session.execute(stmt)).scalars().all())

    async def get_ruleset(
        self, session: AsyncSession, org_id: uuid.UUID, ruleset_id: uuid.UUID
    ) -> RuleSet:
        rs = (
            await session.execute(
                select(RuleSet).where(
                    RuleSet.organization_id == org_id, RuleSet.id == ruleset_id
                )
            )
        ).scalar_one_or_none()
        if not rs:
            raise NotFoundError(f"RuleSet {ruleset_id} not found")
        return rs


regulations_service = RegulationsService()
