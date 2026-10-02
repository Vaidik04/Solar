"""
Solar Operations OS — Supply Chain Module: Public DTOs
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    gstin: Optional[str] = Field(None, max_length=20)
    pan: Optional[str] = Field(None, max_length=15)
    contact_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: dict = Field(default_factory=dict)
    state_code: str = Field(..., max_length=10)


class SupplierOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    state_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WarehouseCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    address: dict = Field(default_factory=dict)
    state_code: str = Field(..., max_length=10)


class WarehouseOut(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    state_code: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class POLineCreate(BaseModel):
    bom_item_id: Optional[uuid.UUID] = None
    item_description: str = Field(..., max_length=255)
    ordered_quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field("NOS", max_length=20)
    unit_price: float = Field(..., ge=0)
    tax_rate_percent: float = Field(18.0, ge=0, le=100)


class PurchaseOrderCreate(BaseModel):
    po_number: str = Field(..., max_length=50)
    supplier_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    currency: str = Field("INR", max_length=10)
    lines: List[POLineCreate] = Field(default_factory=list)


class POLineOut(BaseModel):
    id: uuid.UUID
    item_description: str
    ordered_quantity: float
    received_quantity: float
    unit_of_measure: str
    unit_price: float
    tax_rate_percent: float
    total_amount: float

    model_config = {"from_attributes": True}


class PurchaseOrderOut(BaseModel):
    id: uuid.UUID
    po_number: str
    supplier_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    status: str
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    currency: str
    subtotal_amount: float
    tax_amount: float
    total_amount: float
    lines: List[POLineOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ShipmentLineCreate(BaseModel):
    po_line_id: uuid.UUID
    dispatched_quantity: float = Field(..., gt=0)
    notes: Optional[str] = None


class ShipmentCreate(BaseModel):
    purchase_order_id: uuid.UUID
    destination_warehouse_id: Optional[uuid.UUID] = None
    tracking_number: Optional[str] = Field(None, max_length=100)
    transporter_name: Optional[str] = Field(None, max_length=100)
    lr_number: Optional[str] = Field(None, max_length=100)
    dispatch_date: datetime
    lines: List[ShipmentLineCreate] = Field(default_factory=list)


class ShipmentOut(BaseModel):
    id: uuid.UUID
    purchase_order_id: uuid.UUID
    status: str
    tracking_number: Optional[str] = None
    dispatch_date: datetime
    delivered_date: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
