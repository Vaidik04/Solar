"""
Solar Operations OS — Warranty Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class WarrantyRegistered:
    event_type: str = field(default="warranty.registered", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    warranty_id: uuid.UUID = uuid.UUID(int=0)
    warranty_type: str = ""
    provider_name: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WarrantyClaimOpened:
    event_type: str = field(default="warranty.claim.opened", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    warranty_id: uuid.UUID = uuid.UUID(int=0)
    claim_id: uuid.UUID = uuid.UUID(int=0)
    claim_number: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WarrantyClaimStatusUpdated:
    event_type: str = field(default="warranty.claim.status_updated", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    claim_id: uuid.UUID = uuid.UUID(int=0)
    claim_number: str = ""
    new_status: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
