"""
Solar Operations OS — Platform Module: Database Models
Owns: AuditEvent, AuditCheckpoint, OutboxEvent, Job, FeatureFlag, Notification, ExportJob, IdempotencyKey
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class OutboxStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"  # exceeded max retries


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


# ── Audit Event (append-only, tamper-evident hash chain) ──────────────────────
class AuditEvent(Base):
    """
    ADR-004: Append-only audit log with per-tenant hash chain.

    DB constraints:
    - REVOKE UPDATE, DELETE ON audit_event FROM app_user (enforced in migration)
    - sequence_num is gapless per organization (enforced by advisory lock in service)
    - prev_hash forms a chain; NULL only for the first event per tenant
    """

    __tablename__ = "audit_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_num: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Hash chain fields
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # NULL for first
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "sequence_num", name="uq_audit_org_sequence"),
        Index("ix_audit_organization_sequence", "organization_id", "sequence_num"),
        Index("ix_audit_subject", "organization_id", "subject_type", "subject_id"),
        Index("ix_audit_actor", "organization_id", "actor_user_id"),
        Index("ix_audit_event_type", "organization_id", "event_type"),
        # BRIN index for time-range queries on large tables
        # (Created via raw SQL in migration — SQLAlchemy doesn't support BRIN natively)
    )


# ── Audit Checkpoint (signed chain head) ──────────────────────────────────────
class AuditCheckpoint(Base):
    """
    Periodically signed checkpoint anchoring the audit chain head.
    The HMAC is signed with a key stored outside the database (secret manager).
    Even if DB is fully restored from backup, a replayed/missing checkpoint is detectable.
    """

    __tablename__ = "audit_checkpoint"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_num: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chain_head_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hmac_signature: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_checkpoint_organization", "organization_id", "created_at"),
    )


# ── Outbox Event ──────────────────────────────────────────────────────────────
class OutboxEvent(Base, TimestampMixin):
    """
    ADR-003: Transactional outbox for reliable domain event delivery.
    Written in the same transaction as the state change.
    """

    __tablename__ = "outbox_event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OutboxStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliver_after: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_outbox_pending",
            "status",
            "deliver_after",
            postgresql_where="status = 'pending'",  # partial index
        ),
        Index("ix_outbox_organization_id", "organization_id"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )


# ── Background Job ────────────────────────────────────────────────────────────
class Job(Base, TimestampMixin):
    __tablename__ = "job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.QUEUED)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    arq_job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_job_organization_id", "organization_id"),
        Index("ix_job_status", "status"),
        Index("ix_job_type_status", "job_type", "status"),
        UniqueConstraint("organization_id", "idempotency_key", name="uq_job_idempotency"),
    )


# ── Feature Flag ──────────────────────────────────────────────────────────────
class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flag"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # Scope: can be platform-wide (org_id NULL) or per-org
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_plan: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=100)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("flag_key", "organization_id", name="uq_feature_flag_key_org"),
        Index("ix_feature_flag_key", "flag_key"),
    )


# ── Notification ──────────────────────────────────────────────────────────────
class Notification(Base, TimestampMixin):
    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NotificationStatus.PENDING
    )
    channels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_notification_recipient", "organization_id", "recipient_user_id", "status"),
        Index("ix_notification_rls", "organization_id"),
    )


# ── Export Job ────────────────────────────────────────────────────────────────
class ExportJob(Base, TimestampMixin):
    __tablename__ = "export_job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    export_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.QUEUED)
    file_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_export_job_rls", "organization_id"),
        Index("ix_export_job_status", "organization_id", "status"),
    )
