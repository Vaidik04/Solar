"""
Solar Operations OS — Workflow FSM & Stage Guard Engine
Pure deterministic finite-state machine governing project lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from app.modules.project.models import Project, ProjectStage


# ── Stage Graph & Allowed Next Stages ─────────────────────────────────────────
STAGE_TRANSITIONS: Dict[str, Set[str]] = {
    ProjectStage.LEAD: {ProjectStage.SITE_SURVEY, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.SITE_SURVEY: {ProjectStage.ENGINEERING_DESIGN, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.ENGINEERING_DESIGN: {ProjectStage.PROPOSAL_ACCEPTED, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.PROPOSAL_ACCEPTED: {ProjectStage.DISCOM_APPLICATION, ProjectStage.PROCUREMENT, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.DISCOM_APPLICATION: {ProjectStage.PROCUREMENT, ProjectStage.INSTALLATION, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.PROCUREMENT: {ProjectStage.INSTALLATION, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.INSTALLATION: {ProjectStage.TESTING_INSPECTION, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.TESTING_INSPECTION: {ProjectStage.WCR_GENERATION, ProjectStage.INSTALLATION, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.WCR_GENERATION: {ProjectStage.COMMISSIONING, ProjectStage.TESTING_INSPECTION, ProjectStage.CANCELLED, ProjectStage.ON_HOLD},
    ProjectStage.COMMISSIONING: {ProjectStage.HANDOVER, ProjectStage.TESTING_INSPECTION, ProjectStage.CANCELLED},
    ProjectStage.HANDOVER: {ProjectStage.OAM_ACTIVE, ProjectStage.CANCELLED},
    ProjectStage.OAM_ACTIVE: {ProjectStage.CANCELLED},  # terminal or active service stage
    ProjectStage.ON_HOLD: {  # Can resume to previous or progress
        ProjectStage.LEAD, ProjectStage.SITE_SURVEY, ProjectStage.ENGINEERING_DESIGN,
        ProjectStage.PROPOSAL_ACCEPTED, ProjectStage.DISCOM_APPLICATION, ProjectStage.PROCUREMENT,
        ProjectStage.INSTALLATION, ProjectStage.TESTING_INSPECTION, ProjectStage.WCR_GENERATION,
        ProjectStage.COMMISSIONING, ProjectStage.CANCELLED
    },
    ProjectStage.CANCELLED: set(),  # Terminal state
}

# Standard SLA hours per stage
STAGE_SLA_HOURS: Dict[str, float] = {
    ProjectStage.LEAD: 48.0,
    ProjectStage.SITE_SURVEY: 72.0,
    ProjectStage.ENGINEERING_DESIGN: 96.0,
    ProjectStage.PROPOSAL_ACCEPTED: 48.0,
    ProjectStage.DISCOM_APPLICATION: 240.0,  # 10 days
    ProjectStage.PROCUREMENT: 168.0,         # 7 days
    ProjectStage.INSTALLATION: 120.0,        # 5 days
    ProjectStage.TESTING_INSPECTION: 48.0,
    ProjectStage.WCR_GENERATION: 24.0,
    ProjectStage.COMMISSIONING: 48.0,
    ProjectStage.HANDOVER: 48.0,
}


@dataclass
class GuardEvaluation:
    guard_name: str
    passed: bool
    explanation: str


@dataclass
class TransitionCheckResult:
    allowed: bool
    reasons: List[str] = field(default_factory=list)
    guard_evaluations: List[GuardEvaluation] = field(default_factory=list)


class WorkflowEngine:
    @staticmethod
    def can_transition(
        from_stage: str,
        to_stage: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TransitionCheckResult:
        """
        Determines whether a stage transition is valid and all required guards pass.
        Pure computation — no external database queries.
        """
        ctx = context or {}
        evaluations: List[GuardEvaluation] = []
        failures: List[str] = []

        # 1. Structural graph transition check
        allowed_next = STAGE_TRANSITIONS.get(from_stage, set())
        if to_stage not in allowed_next and from_stage != to_stage:
            failures.append(f"Transition from '{from_stage}' to '{to_stage}' is not permitted by workflow DAG")
            return TransitionCheckResult(allowed=False, reasons=failures)

        # 2. Stage-Specific Guards
        # Guard: SITE_SURVEY -> ENGINEERING_DESIGN (Site survey must be verified/completed)
        if to_stage == ProjectStage.ENGINEERING_DESIGN:
            survey_completed = ctx.get("survey_completed", True)
            passed = bool(survey_completed)
            evaluations.append(
                GuardEvaluation(
                    guard_name="survey_completed",
                    passed=passed,
                    explanation="Site survey must be completed and marked structurally viable before engineering design"
                    if not passed
                    else "Site survey is complete",
                )
            )
            if not passed:
                failures.append(evaluations[-1].explanation)

        # Guard: -> DISCOM_APPLICATION (Requires customer utility consumer number)
        if to_stage == ProjectStage.DISCOM_APPLICATION:
            has_consumer_number = bool(ctx.get("consumer_number"))
            evaluations.append(
                GuardEvaluation(
                    guard_name="has_consumer_number",
                    passed=has_consumer_number,
                    explanation="Customer DISCOM consumer number is required to file grid interconnection"
                    if not has_consumer_number
                    else "Consumer number present",
                )
            )
            if not has_consumer_number:
                failures.append(evaluations[-1].explanation)

        # Guard: -> INSTALLATION (Requires finalized BOM / design)
        if to_stage == ProjectStage.INSTALLATION:
            bom_finalized = ctx.get("bom_finalized", True)
            passed = bool(bom_finalized)
            evaluations.append(
                GuardEvaluation(
                    guard_name="bom_finalized",
                    passed=passed,
                    explanation="Bill of Materials (BOM) must be finalized before commencing site installation"
                    if not passed
                    else "BOM finalized",
                )
            )
            if not passed:
                failures.append(evaluations[-1].explanation)

        # Guard: -> COMMISSIONING (Requires generated Work Completion Report - WCR)
        if to_stage == ProjectStage.COMMISSIONING:
            wcr_approved = ctx.get("wcr_approved", True)
            passed = bool(wcr_approved)
            evaluations.append(
                GuardEvaluation(
                    guard_name="wcr_approved",
                    passed=passed,
                    explanation="Approved Work Completion Report (WCR) is required for plant commissioning"
                    if not passed
                    else "WCR approved",
                )
            )
            if not passed:
                failures.append(evaluations[-1].explanation)

        return TransitionCheckResult(
            allowed=len(failures) == 0,
            reasons=failures,
            guard_evaluations=evaluations,
        )

    @staticmethod
    def calculate_stage_duration_and_sla(
        stage: str,
        stage_entered_at: datetime,
        now: Optional[datetime] = None,
    ) -> Tuple[int, float, bool]:
        """
        Returns:
            (duration_seconds, hours_in_stage, is_sla_breached)
        """
        current_time = now or datetime.now(timezone.utc)
        duration_seconds = int((current_time - stage_entered_at).total_seconds())
        hours_in_stage = duration_seconds / 3600.0
        sla_hours = STAGE_SLA_HOURS.get(stage, 168.0)
        is_breached = hours_in_stage > sla_hours
        return duration_seconds, hours_in_stage, is_breached


workflow_engine = WorkflowEngine()
