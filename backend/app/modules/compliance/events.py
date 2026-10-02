"""
Solar Operations OS — Compliance Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ComplianceRunStarted:
    event_type: str = field(default="compliance.run.started", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    run_id: uuid.UUID = uuid.UUID(int=0)
    rule_set_id: uuid.UUID | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ComplianceRunCompleted:
    event_type: str = field(default="compliance.run.completed", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    run_id: uuid.UUID = uuid.UUID(int=0)
    passed: int = 0
    failed: int = 0
    warned: int = 0
    total_rules: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ComplianceWaiverGranted:
    event_type: str = field(default="compliance.waiver.granted", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    waiver_id: uuid.UUID = uuid.UUID(int=0)
    rule_code: str = ""
    granted_by_user_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
