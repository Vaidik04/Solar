"""
Solar Operations OS — CRM & Sites Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.events import DomainEvent


@dataclass
class CustomerCreated(DomainEvent):
    customer_id: uuid.UUID = uuid.UUID(int=0)
    customer_type: str = ""
    name: str = ""
    phone: str = ""


@dataclass
class CustomerUpdated(DomainEvent):
    customer_id: uuid.UUID = uuid.UUID(int=0)
    name: str = ""
    kyc_status: str = ""


@dataclass
class SiteCreated(DomainEvent):
    site_id: uuid.UUID = uuid.UUID(int=0)
    customer_id: uuid.UUID = uuid.UUID(int=0)
    name: str = ""
    state_code: str = ""
    pincode: str = ""
    sanctioned_load_kw: float = 0.0


@dataclass
class SiteUpdated(DomainEvent):
    site_id: uuid.UUID = uuid.UUID(int=0)
    sanctioned_load_kw: float = 0.0
    usable_roof_area_sqft: float = 0.0


@dataclass
class SiteSurveyCompleted(DomainEvent):
    survey_id: uuid.UUID = uuid.UUID(int=0)
    site_id: uuid.UUID = uuid.UUID(int=0)
    surveyor_user_id: uuid.UUID = uuid.UUID(int=0)
    recommended_capacity_kw: Optional[float] = None
    structural_viability: bool = True
