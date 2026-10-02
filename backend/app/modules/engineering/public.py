"""
Solar Operations OS — Engineering Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class StringConfigCreate(BaseModel):
    string_number: int = Field(..., ge=1)
    inverter_index: int = Field(1, ge=1)
    mppt_tracker_index: int = Field(1, ge=1)
    panels_count: int = Field(..., ge=1)
    vmp_volts: Optional[float] = None
    voc_volts: Optional[float] = None
    imp_amps: Optional[float] = None
    isc_amps: Optional[float] = None


class DesignCreate(BaseModel):
    project_id: uuid.UUID
    name: str = Field("Preliminary Design", max_length=100)
    system_type: str = Field("grid_tied")
    capacity_kw_dc: float = Field(..., gt=0)
    capacity_kw_ac: float = Field(..., gt=0)
    panel_make: str = Field(..., max_length=100)
    panel_model: str = Field(..., max_length=100)
    panel_wattage: float = Field(..., gt=0)
    panel_count: int = Field(..., ge=1)
    inverter_make: str = Field(..., max_length=100)
    inverter_model: str = Field(..., max_length=100)
    inverter_count: int = Field(..., ge=1)
    tilt_degrees: float = Field(15.0, ge=0, le=90)
    azimuth_degrees: float = Field(180.0, ge=0, le=360)
    expected_annual_generation_kwh: Optional[float] = None
    performance_ratio_percent: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    string_configurations: List[StringConfigCreate] = Field(default_factory=list)


class DesignUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    expected_annual_generation_kwh: Optional[float] = None
    performance_ratio_percent: Optional[float] = Field(None, ge=0, le=100)


class DesignOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    design_version: int
    name: str
    system_type: str
    status: str
    capacity_kw_dc: float
    capacity_kw_ac: float
    panel_make: str
    panel_model: str
    panel_wattage: float
    panel_count: int
    inverter_make: str
    inverter_model: str
    inverter_count: int
    tilt_degrees: float
    azimuth_degrees: float
    expected_annual_generation_kwh: Optional[float] = None
    performance_ratio_percent: Optional[float] = None
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BOMItemCreate(BaseModel):
    category: str
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., max_length=255)
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field("NOS", max_length=20)
    is_serialized: bool = False


class BOMCreate(BaseModel):
    project_id: uuid.UUID
    design_id: uuid.UUID
    items: List[BOMItemCreate] = Field(default_factory=list)


class BOMItemOut(BaseModel):
    id: uuid.UUID
    category: str
    item_code: Optional[str] = None
    description: str
    make: str
    model: str
    specifications: Dict[str, Any]
    quantity: float
    unit_of_measure: str
    is_serialized: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BOMOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    design_id: uuid.UUID
    bom_version: int
    status: str
    finalized_at: Optional[datetime] = None
    items: List[BOMItemOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}
