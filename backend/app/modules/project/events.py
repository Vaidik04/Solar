"""
Solar Operations OS — Project Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.events import DomainEvent


@dataclass
class ProjectCreated(DomainEvent):
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    customer_id: uuid.UUID = uuid.UUID(int=0)
    site_id: uuid.UUID = uuid.UUID(int=0)
    capacity_kw_dc: float = 0.0
    capacity_kw_ac: float = 0.0


@dataclass
class ProjectStageTransitioned(DomainEvent):
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    from_stage: str = ""
    to_stage: str = ""
    actor_user_id: Optional[uuid.UUID] = None
    is_override: bool = False


@dataclass
class ProjectStuck(DomainEvent):
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    current_stage: str = ""
    hours_in_stage: float = 0.0
    sla_hours: float = 0.0


@dataclass
class ProjectCompleted(DomainEvent):
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    customer_id: uuid.UUID = uuid.UUID(int=0)
    site_id: uuid.UUID = uuid.UUID(int=0)
    capacity_kw_dc: float = 0.0


@dataclass
class DiscomApplicationSubmitted(DomainEvent):
    application_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    discom_name: str = ""
    application_number: str = ""


@dataclass
class DiscomApplicationApproved(DomainEvent):
    application_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    discom_name: str = ""
    sanctioned_capacity_kw: float = 0.0
