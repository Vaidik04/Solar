"""
Solar Operations OS — Compliance Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplianceRunTrigger(BaseModel):
    project_id: uuid.UUID
    rule_set_id: Optional[uuid.UUID] = None
    context_override: Dict[str, Any] = Field(default_factory=dict)


class ComplianceResultOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    rule_id: Optional[uuid.UUID] = None
    rule_code: str
    rule_title: str
    status: str
    message: Optional[str] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    waiver_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceRunOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    rule_set_id: Optional[uuid.UUID] = None
    triggered_by_user_id: Optional[uuid.UUID] = None
    triggered_by_event: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_rules: int
    passed: int
    failed: int
    warned: int
    error_message: Optional[str] = None
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    results: List[ComplianceResultOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceWaiverCreate(BaseModel):
    project_id: uuid.UUID
    rule_code: str = Field(..., max_length=100)
    reason: str = Field(..., min_length=5)
    expires_at: Optional[datetime] = None


class ComplianceWaiverOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    rule_code: str
    reason: str
    granted_by_user_id: uuid.UUID
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
