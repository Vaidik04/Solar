"""
Solar Operations OS — Asset Public Schemas (DTOs)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.assets.models import AssetCategory, AssetEventType, AssetStatus


# ── Asset Type DTOs ───────────────────────────────────────────────────────────
class AssetTypeBase(BaseModel):
    category: AssetCategory
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    nominal_rating_kw: Optional[float] = Field(None, gt=0)
    warranty_months: int = Field(60, ge=0)
    is_serialized: bool = True
    specifications: Dict[str, Any] = Field(default_factory=dict)


class AssetTypeCreate(AssetTypeBase):
    pass


class AssetTypeRead(AssetTypeBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Asset Event DTO ───────────────────────────────────────────────────────────
class AssetEventRead(BaseModel):
    id: uuid.UUID
    event_type: AssetEventType
    actor_user_id: Optional[uuid.UUID] = None
    recorded_at: datetime
    description: Optional[str] = None
    event_payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ── Asset DTOs ────────────────────────────────────────────────────────────────
class AssetRegister(BaseModel):
    asset_type_id: uuid.UUID
    serial_number: str = Field(..., min_length=3, max_length=100)
    location_tag: Optional[str] = None
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)


class AssetAllocate(BaseModel):
    project_id: uuid.UUID
    location_tag: Optional[str] = None


class AssetInstall(BaseModel):
    location_tag: str = Field(..., min_length=2, max_length=100)
    installed_at: Optional[datetime] = None


class AssetReplace(BaseModel):
    replacement_asset_id: uuid.UUID
    reason: str = Field(..., min_length=5)


class AssetRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    asset_type_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    plant_id: Optional[str] = None
    serial_number: str
    normalized_serial: str
    qr_token: str
    status: AssetStatus
    location_tag: Optional[str] = None
    installed_at: Optional[datetime] = None
    commissioned_at: Optional[datetime] = None
    metadata_fields: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    events: List[AssetEventRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
