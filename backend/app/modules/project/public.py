"""
Solar Operations OS — Project Public Schemas (DTOs)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.project.models import DiscomAppStatus, ProjectStage, ProjectStatus


# ── Stage History DTO ─────────────────────────────────────────────────────────
class StageHistoryRead(BaseModel):
    id: uuid.UUID
    from_stage: str
    to_stage: str
    transitioned_at: datetime
    actor_user_id: Optional[uuid.UUID] = None
    duration_in_stage_seconds: Optional[int] = None
    transition_reason: Optional[str] = None
    guard_results: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ── Project DTOs ──────────────────────────────────────────────────────────────
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    customer_id: uuid.UUID
    site_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    manager_user_id: Optional[uuid.UUID] = None
    capacity_kw_dc: float = Field(..., gt=0)
    capacity_kw_ac: float = Field(..., gt=0)
    estimated_annual_kwh: Optional[float] = Field(None, gt=0)
    target_commissioning_date: Optional[datetime] = None
    project_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    manager_user_id: Optional[uuid.UUID] = None
    capacity_kw_dc: Optional[float] = Field(None, gt=0)
    capacity_kw_ac: Optional[float] = Field(None, gt=0)
    estimated_annual_kwh: Optional[float] = None
    target_commissioning_date: Optional[datetime] = None
    status: Optional[ProjectStatus] = None
    project_metadata: Optional[Dict[str, Any]] = None


class ProjectTransition(BaseModel):
    to_stage: ProjectStage
    reason: Optional[str] = None


class ProjectTransitionOverride(BaseModel):
    to_stage: ProjectStage
    reason: str = Field(..., min_length=10, description="Justification for bypassing stage guards")


class ProjectRead(ProjectBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    plant_id: str
    current_stage: ProjectStage
    status: ProjectStatus
    stage_entered_at: datetime
    actual_commissioning_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    stage_histories: List[StageHistoryRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ── Application DTOs ──────────────────────────────────────────────────────────
class ApplicationBase(BaseModel):
    project_id: uuid.UUID
    discom_name: str = Field(..., max_length=100)
    application_number: str = Field(..., max_length=100)
    consumer_number: str = Field(..., max_length=100)
    feeder_code: Optional[str] = None
    dt_code: Optional[str] = None
    applied_capacity_kw: float = Field(..., gt=0)
    sanctioned_capacity_kw: Optional[float] = None
    discom_fee_amount: Optional[float] = None
    discom_fee_receipt_ref: Optional[str] = None
    notes: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    status: DiscomAppStatus
    submission_date: Optional[datetime] = None
    approval_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
