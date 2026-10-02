"""
Solar Operations OS — Regulations Module: Database Models
Owns: Authority, Regulation, RegulationVersion, Rule, RuleVersion, RuleSet
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin, VersionMixin


class AuthorityLevel(StrEnum):
    CENTRAL = "central"       # MNRE, CEA
    STATE = "state"           # SERC, DISCOM
    LOCAL = "local"           # Municipality, CEIG


class RuleType(StrEnum):
    DOCUMENT_REQUIRED = "document_required"
    CAPACITY_LIMIT = "capacity_limit"
    TECHNICAL_STANDARD = "technical_standard"
    SUBSIDY_ELIGIBILITY = "subsidy_eligibility"
    NET_METERING_REQUIREMENT = "net_metering_requirement"
    APPROVAL_WORKFLOW = "approval_workflow"


class RuleStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


# ── Authority ─────────────────────────────────────────────────────────────────
class Authority(Base, TenantMixin, TimestampMixin):
    __tablename__ = "authority"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False, default=AuthorityLevel.STATE)
    state_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # None = central
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    regulations: Mapped[list[Regulation]] = relationship("Regulation", back_populates="authority")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_authority_org_code"),
        Index("ix_authority_level", "organization_id", "level"),
    )


# ── Regulation ────────────────────────────────────────────────────────────────
class Regulation(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "regulation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authority_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("authority.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    applies_to_states: Mapped[list[str]] = mapped_column(
        ARRAY(String(10)), nullable=False, default=list
    )  # Empty = all states

    authority: Mapped[Authority] = relationship("Authority", back_populates="regulations")
    rules: Mapped[list[Rule]] = relationship("Rule", back_populates="regulation")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_regulation_org_code"),
        Index("ix_regulation_authority", "organization_id", "authority_id"),
    )


# ── Rule ──────────────────────────────────────────────────────────────────────
class Rule(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "rule"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulation.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RuleStatus.ACTIVE)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # DSL expression – JSON logic or YAML predicate
    condition_dsl: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Action/constraint metadata
    action_meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Capacity thresholds (kW)
    min_capacity_kw: Mapped[Optional[float]] = mapped_column(String(20), nullable=True)
    max_capacity_kw: Mapped[Optional[float]] = mapped_column(String(20), nullable=True)
    applies_to_system_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(30)), nullable=False, default=list
    )  # Empty = all types

    regulation: Mapped[Regulation] = relationship("Regulation", back_populates="rules")

    __table_args__ = (
        UniqueConstraint("regulation_id", "code", name="uq_rule_reg_code"),
        Index("ix_rule_type", "organization_id", "rule_type"),
        Index("ix_rule_status", "organization_id", "status"),
    )


# ── Rule Set (grouping rules for a state/project-type) ───────────────────────
class RuleSet(Base, TenantMixin, TimestampMixin):
    __tablename__ = "rule_set"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    system_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rule_ids: Mapped[list[str]] = mapped_column(ARRAY(String(36)), nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_ruleset_org_code"),
    )
