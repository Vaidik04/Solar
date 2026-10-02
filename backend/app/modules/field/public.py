"""
Solar Operations OS — Field Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Meter ─────────────────────────────────────────────────────────────────────
class MeterCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    meter_type: str = Field("net_meter", max_length=50)
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    serial_number: str = Field(..., max_length=100)
    meter_number: Optional[str] = Field(None, max_length=100)
    discom_asset_id: Optional[str] = Field(None, max_length=100)
    capacity_kw: Optional[float] = None
    installed_date: Optional[date] = None


class MeterOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    meter_type: str
    make: str
    model: str
    serial_number: str
    meter_number: Optional[str] = None
    discom_asset_id: Optional[str] = None
    capacity_kw: Optional[float] = None
    installed_date: Optional[date] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Inspection Template ───────────────────────────────────────────────────────
class InspectionTemplateCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    checklist: List[Dict[str, Any]] = Field(default_factory=list)


class InspectionTemplateOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    checklist: List[Dict[str, Any]]
    version: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Inspection & Inspection Items ─────────────────────────────────────────────
class InspectionItemCreate(BaseModel):
    check_code: str = Field(..., max_length=100)
    label: str = Field(..., max_length=255)
    result: Optional[str] = Field("pass", max_length=50)
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    photo_storage_key: Optional[str] = None
    remarks: Optional[str] = None


class InspectionItemOut(BaseModel):
    id: uuid.UUID
    check_code: str
    label: str
    result: Optional[str] = None
    numeric_value: Optional[float] = None
    text_value: Optional[str] = None
    photo_storage_key: Optional[str] = None
    remarks: Optional[str] = None

    model_config = {"from_attributes": True}


class InspectionCreate(BaseModel):
    project_id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    inspector_user_id: Optional[uuid.UUID] = None
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None


class InspectionSubmit(BaseModel):
    conducted_date: date
    items: List[InspectionItemCreate]
    notes: Optional[str] = None
    geo_location: Optional[Dict[str, Any]] = None


class InspectionOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    template_id: Optional[uuid.UUID] = None
    inspector_user_id: Optional[uuid.UUID] = None
    scheduled_date: Optional[date] = None
    conducted_date: Optional[date] = None
    status: str
    score_percent: Optional[float] = None
    overall_result: Optional[str] = None
    notes: Optional[str] = None
    geo_location: Optional[Dict[str, Any]] = None
    items: List[InspectionItemOut] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


# ── WCR ───────────────────────────────────────────────────────────────────────
class WCRCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    capacity_installed_kw: float = Field(..., gt=0)
    asset_ids: List[str] = Field(default_factory=list)
    completion_date: Optional[date] = None
    document_storage_key: Optional[str] = None
    document_sha256: Optional[str] = None


class WCROut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    wcr_number: str
    wcr_version: int
    status: str
    completion_date: Optional[date] = None
    capacity_installed_kw: float
    asset_ids: List[str]
    document_storage_key: Optional[str] = None
    document_sha256: Optional[str] = None
    submitted_by_user_id: Optional[uuid.UUID] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Commissioning ─────────────────────────────────────────────────────────────
class CommissioningCreate(BaseModel):
    project_id: uuid.UUID
    plant_id: str = Field(..., max_length=50)
    commissioned_date: date
    grid_synchronization_date: Optional[date] = None
    initial_generation_kwh: Optional[float] = None
    test_results: Dict[str, Any] = Field(default_factory=dict)
    checklist_results: Dict[str, Any] = Field(default_factory=dict)
    discom_approval_reference: Optional[str] = None
    remarks: Optional[str] = None


class CommissioningOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    plant_id: str
    status: str
    commissioned_date: Optional[date] = None
    commissioned_by_user_id: Optional[uuid.UUID] = None
    grid_synchronization_date: Optional[date] = None
    initial_generation_kwh: Optional[float] = None
    test_results: Dict[str, Any]
    checklist_results: Dict[str, Any]
    discom_approval_reference: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
