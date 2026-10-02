"""
Solar Operations OS — Supply Chain Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class POCreated:
    event_type: str = field(default="supply.po.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    po_id: uuid.UUID = uuid.UUID(int=0)
    po_number: str = ""
    supplier_id: uuid.UUID = uuid.UUID(int=0)
    total_amount: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ShipmentReceived:
    event_type: str = field(default="supply.shipment.received", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    shipment_id: uuid.UUID = uuid.UUID(int=0)
    po_id: uuid.UUID = uuid.UUID(int=0)
    warehouse_id: uuid.UUID | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StockAllocated:
    event_type: str = field(default="supply.stock.allocated", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    asset_id: uuid.UUID = uuid.UUID(int=0)
    to_project_id: uuid.UUID | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StockAdjusted:
    event_type: str = field(default="supply.stock.adjusted", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    movement_id: uuid.UUID = uuid.UUID(int=0)
    movement_type: str = ""
    quantity: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
