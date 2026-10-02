"""
Solar Operations OS — CRM Public Schemas (DTOs)
Only types defined here or in .service may be referenced by other modules.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.crm.models import CustomerType, KycStatus, PhotoCategory, RoofType, SurveyStatus


# ── Customer Schemas ──────────────────────────────────────────────────────────
class ContactBase(BaseModel):
    name: str = Field(..., max_length=255)
    designation: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: str = Field(..., max_length=20)
    is_primary: bool = False


class ContactCreate(ContactBase):
    pass


class ContactRead(ContactBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    customer_type: CustomerType = CustomerType.RESIDENTIAL
    name: str = Field(..., min_length=2, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    pan_number: Optional[str] = Field(None, max_length=15)
    gst_number: Optional[str] = Field(None, max_length=20)
    billing_address: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    contacts: List[ContactCreate] = Field(default_factory=list)


class CustomerUpdate(BaseModel):
    customer_type: Optional[CustomerType] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    company_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    pan_number: Optional[str] = None
    gst_number: Optional[str] = None
    kyc_status: Optional[KycStatus] = None
    billing_address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CustomerRead(CustomerBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    kyc_status: KycStatus
    created_at: datetime
    updated_at: datetime
    contacts: List[ContactRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ── Site Schemas ──────────────────────────────────────────────────────────────
class SiteBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    customer_id: uuid.UUID
    branch_id: Optional[uuid.UUID] = None
    address: Dict[str, Any] = Field(default_factory=dict)
    state_code: str = Field(..., min_length=2, max_length=10)
    pincode: str = Field(..., min_length=5, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    # Electrical
    discom_name: str = Field(..., max_length=100)
    consumer_number: str = Field(..., max_length=100)
    meter_number: Optional[str] = Field(None, max_length=100)
    sanctioned_load_kw: float = Field(..., gt=0)
    tariff_category: Optional[str] = Field(None, max_length=50)
    transformer_capacity_kva: Optional[float] = None
    supply_voltage_kv: Optional[float] = 0.415

    # Structural
    roof_type: RoofType = RoofType.RCC_FLAT
    usable_roof_area_sqft: float = Field(..., gt=0)
    tilt_angle_degrees: Optional[float] = Field(None, ge=0, le=90)
    azimuth_degrees: Optional[float] = Field(180.0, ge=0, le=360)
    shading_hazards: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    branch_id: Optional[uuid.UUID] = None
    address: Optional[Dict[str, Any]] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    discom_name: Optional[str] = None
    consumer_number: Optional[str] = None
    meter_number: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    tariff_category: Optional[str] = None
    transformer_capacity_kva: Optional[float] = None
    supply_voltage_kv: Optional[float] = None
    roof_type: Optional[RoofType] = None
    usable_roof_area_sqft: Optional[float] = None
    tilt_angle_degrees: Optional[float] = None
    azimuth_degrees: Optional[float] = None
    shading_hazards: Optional[Dict[str, Any]] = None


class SiteRead(SiteBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Site Survey Schemas ───────────────────────────────────────────────────────
class SiteSurveyCreate(BaseModel):
    surveyor_user_id: uuid.UUID
    survey_date: datetime
    structural_viability: bool = True
    recommended_capacity_kw: Optional[float] = Field(None, gt=0)
    electrical_assessment: Dict[str, Any] = Field(default_factory=dict)
    shadow_analysis: Dict[str, Any] = Field(default_factory=dict)
    gps_verified: bool = False
    survey_coordinates: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class SiteSurveyRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    surveyor_user_id: uuid.UUID
    status: SurveyStatus
    survey_date: datetime
    structural_viability: bool
    recommended_capacity_kw: Optional[float]
    electrical_assessment: Dict[str, Any]
    shadow_analysis: Dict[str, Any]
    gps_verified: bool
    survey_coordinates: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Site Photo Schemas ────────────────────────────────────────────────────────
class SitePhotoRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    site_id: uuid.UUID
    survey_id: Optional[uuid.UUID]
    uploader_user_id: uuid.UUID
    category: PhotoCategory
    caption: Optional[str]
    storage_key: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    exif_latitude: Optional[float]
    exif_longitude: Optional[float]
    exif_captured_at: Optional[datetime]
    compass_bearing_degrees: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
