"""
Solar Operations OS — Engineering Module Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DesignCreated:
    event_type: str = field(default="engineering.design.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    design_id: uuid.UUID = uuid.UUID(int=0)
    design_version: int = 1
    capacity_kw_dc: float = 0.0
    system_type: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DesignApproved:
    event_type: str = field(default="engineering.design.approved", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    design_id: uuid.UUID = uuid.UUID(int=0)
    approved_by_user_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DesignRevised:
    event_type: str = field(default="engineering.design.revised", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    design_id: uuid.UUID = uuid.UUID(int=0)
    new_version: int = 2
    revised_by_user_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BOMFinalised:
    event_type: str = field(default="engineering.bom.finalised", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    bom_id: uuid.UUID = uuid.UUID(int=0)
    bom_version: int = 1
    item_count: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
