"""
Solar Operations OS — Regulations Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RegulationCreated:
    event_type: str = field(default="regulations.regulation.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    regulation_id: uuid.UUID = uuid.UUID(int=0)
    code: str = ""
    authority_id: uuid.UUID = uuid.UUID(int=0)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RuleCreated:
    event_type: str = field(default="regulations.rule.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    regulation_id: uuid.UUID = uuid.UUID(int=0)
    rule_id: uuid.UUID = uuid.UUID(int=0)
    code: str = ""
    rule_type: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RuleSetCreated:
    event_type: str = field(default="regulations.ruleset.created", init=False)
    organization_id: uuid.UUID = uuid.UUID(int=0)
    rule_set_id: uuid.UUID = uuid.UUID(int=0)
    code: str = ""
    state_code: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
