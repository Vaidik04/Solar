"""
Solar Operations OS — Asset Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.events import DomainEvent


@dataclass
class AssetRegistered(DomainEvent):
    asset_id: uuid.UUID = uuid.UUID(int=0)
    serial_number: str = ""
    category: str = ""
    asset_type_id: uuid.UUID = uuid.UUID(int=0)


@dataclass
class AssetAllocated(DomainEvent):
    asset_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""


@dataclass
class AssetInstalled(DomainEvent):
    asset_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    location_tag: Optional[str] = None


@dataclass
class AssetReplaced(DomainEvent):
    old_asset_id: uuid.UUID = uuid.UUID(int=0)
    new_asset_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    reason: str = ""


@dataclass
class AssetRetired(DomainEvent):
    asset_id: uuid.UUID = uuid.UUID(int=0)
    reason: str = ""
