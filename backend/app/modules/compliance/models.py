"""
Solar Operations OS — Compliance Module: Database Models
Owns: ComplianceRun, ComplianceResult, ComplianceException, ComplianceWaiver
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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TenantMixin, TimestampMixin


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIPPED = "skipped"
    WAIVED = "waived"


# ── Compliance Run ────────────────────────────────────────────────────────────
class ComplianceRun(Base, TenantMixin, TimestampMixin):
    __tablename__ = "compliance_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    rule_set_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    triggered_by_event: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RunStatus.PENDING)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_rules: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    results: Mapped[list[ComplianceResult]] = relationship(
        "ComplianceResult", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_compliance_run_project", "organization_id", "project_id"),
        Index("ix_compliance_run_status", "organization_id", "status"),
    )


# ── Compliance Result ─────────────────────────────────────────────────────────
class ComplianceResult(Base, TenantMixin, TimestampMixin):
    __tablename__ = "compliance_result"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_run.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_title: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ResultStatus.PASS)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    waiver_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    run: Mapped[ComplianceRun] = relationship("ComplianceRun", back_populates="results")

    __table_args__ = (
        Index("ix_compliance_result_run", "run_id"),
        Index("ix_compliance_result_status", "run_id", "status"),
    )


# ── Compliance Waiver ─────────────────────────────────────────────────────────
class ComplianceWaiver(Base, TenantMixin, TimestampMixin):
    __tablename__ = "compliance_waiver"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_waiver_project_rule", "project_id", "rule_code"),
    )
