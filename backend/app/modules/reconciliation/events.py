"""
Solar Operations OS — Reconciliation Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ReconciliationRunStarted:
    event_type: str = field(default="reconciliation.run.started", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    run_id: uuid.UUID = uuid.UUID(int=0)
    scope: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReconciliationRunCompleted:
    event_type: str = field(default="reconciliation.run.completed", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    run_id: uuid.UUID = uuid.UUID(int=0)
    scope: str = ""
    matched: int = 0
    mismatched: int = 0
    total_items: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReconciliationDiscrepancyResolved:
    event_type: str = field(default="reconciliation.discrepancy.resolved", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    run_id: uuid.UUID = uuid.UUID(int=0)
    comparison_id: uuid.UUID = uuid.UUID(int=0)
    resolved_by_user_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
