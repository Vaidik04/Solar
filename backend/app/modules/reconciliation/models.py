"""
Solar Operations OS — Reconciliation Module: Database Models
Owns: ReconciliationRun, ReconciliationComparison, SourceSnapshot
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
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


class ReconciliationScope(StrEnum):
    DESIGN_VS_INSTALLED = "design_vs_installed"
    BOM_VS_INSTALLED = "bom_vs_installed"
    PLANNED_VS_ACTUAL_GENERATION = "planned_vs_actual_generation"
    DOCUMENTS_COMPLETENESS = "documents_completeness"


class ReconciliationRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ComparisonResult(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"
    MISSING_PLANNED = "missing_planned"
    MISSING_ACTUAL = "missing_actual"
    WAIVED = "waived"


# ── Reconciliation Run ────────────────────────────────────────────────────────
class ReconciliationRun(Base, TenantMixin, TimestampMixin):
    __tablename__ = "reconciliation_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ReconciliationRunStatus.PENDING)
    triggered_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    triggered_by_event: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mismatched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    comparisons: Mapped[list[ReconciliationComparison]] = relationship(
        "ReconciliationComparison", back_populates="run", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list[SourceSnapshot]] = relationship(
        "SourceSnapshot", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_recon_run_project", "organization_id", "project_id"),
        Index("ix_recon_run_status", "organization_id", "status"),
    )


# ── Reconciliation Comparison ─────────────────────────────────────────────────
class ReconciliationComparison(Base, TenantMixin, TimestampMixin):
    __tablename__ = "reconciliation_comparison"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_run.id", ondelete="CASCADE"), nullable=False
    )
    item_key: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g., asset serial or BOM item code
    item_type: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False, default=ComparisonResult.MATCH)
    planned_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    actual_value: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    delta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    mismatch_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped[ReconciliationRun] = relationship("ReconciliationRun", back_populates="comparisons")

    __table_args__ = (
        Index("ix_recon_comparison_run", "run_id"),
        Index("ix_recon_comparison_result", "run_id", "result"),
    )


# ── Source Snapshot (immutable capture of planned/actual at run time) ─────────
class SourceSnapshot(Base, TenantMixin, TimestampMixin):
    __tablename__ = "source_snapshot"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliation_run.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "design", "bom", "assets"
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    run: Mapped[ReconciliationRun] = relationship("ReconciliationRun", back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshot_run", "run_id"),
    )
