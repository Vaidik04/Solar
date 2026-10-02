"""
Solar Operations OS — Reconciliation Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReconciliationRunCreate(BaseModel):
    project_id: uuid.UUID
    scope: str = Field("bom_vs_installed", max_length=50)


class ReconciliationComparisonOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    item_key: str
    item_type: str
    result: str
    planned_value: Optional[Dict[str, Any]] = None
    actual_value: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None
    mismatch_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by_user_id: Optional[uuid.UUID] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceSnapshotOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    source_type: str
    sha256_hash: str
    captured_at: datetime

    model_config = {"from_attributes": True}


class ReconciliationRunOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    scope: str
    status: str
    triggered_by_user_id: Optional[uuid.UUID] = None
    triggered_by_event: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_items: int
    matched: int
    mismatched: int
    summary: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    comparisons: List[ReconciliationComparisonOut] = Field(default_factory=list)
    snapshots: List[SourceSnapshotOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class ResolveDiscrepancyRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3)
    override_result: str = Field("waived")  # waived or match
