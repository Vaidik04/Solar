"""
Solar Operations OS — Warranty Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Warranty ──────────────────────────────────────────────────────────────────
class WarrantyCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    asset_id: Optional[uuid.UUID] = None
    warranty_type: str = Field("comprehensive", max_length=50)
    provider_name: str = Field(..., max_length=255)
    certificate_number: Optional[str] = Field(None, max_length=100)
    start_date: date
    end_date: date
    period_years: int = Field(..., ge=1)
    coverage_details: str = Field(..., min_length=5)
    exclusions: Optional[str] = None
    document_storage_key: Optional[str] = None
    document_sha256: Optional[str] = None


class WarrantyOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    asset_id: Optional[uuid.UUID] = None
    warranty_type: str
    provider_name: str
    certificate_number: Optional[str] = None
    start_date: date
    end_date: date
    period_years: int
    coverage_details: str
    exclusions: Optional[str] = None
    document_storage_key: Optional[str] = None
    document_sha256: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Claim Events & Claim ──────────────────────────────────────────────────────
class ClaimEventOut(BaseModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    event_type: str
    description: str
    actor_user_id: Optional[uuid.UUID] = None
    event_meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class WarrantyClaimCreate(BaseModel):
    warranty_id: uuid.UUID
    defect_description: str = Field(..., min_length=10)
    affected_components: List[str] = Field(default_factory=list)


class WarrantyClaimStatusUpdate(BaseModel):
    status: str = Field(..., max_length=50)
    notes: Optional[str] = None
    replacement_asset_ids: Optional[List[str]] = None


class WarrantyClaimOut(BaseModel):
    id: uuid.UUID
    warranty_id: uuid.UUID
    claim_number: str
    opened_date: date
    status: str
    defect_description: str
    affected_components: List[str]
    reported_by_user_id: Optional[uuid.UUID] = None
    resolved_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    replacement_asset_ids: List[str]
    events: List[ClaimEventOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}
