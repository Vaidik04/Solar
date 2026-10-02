"""
Solar Operations OS — Identity Module: Database Models
Owns: Organization, Branch, Team, User, Role, Permission, Membership, Session, Device, ApiKey
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, SoftDeleteMixin, TimestampMixin, VersionMixin


# ── Enums ─────────────────────────────────────────────────────────────────────
class OrgPlan(StrEnum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class OrgStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_INVITE = "pending_invite"
    LOCKED = "locked"  # brute-force lockout


class SessionStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ── Organization ──────────────────────────────────────────────────────────────
class Organization(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "organization"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # e.g. "MH" for Maharashtra — used in Plant ID generation
    state_code: Mapped[str] = mapped_column(String(10), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default=OrgPlan.STARTER)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=OrgStatus.TRIAL)
    # SSO configuration (seam for future IdP integration)
    sso_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sso_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sso_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Feature flags override at org level
    feature_flags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    # Contact
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Billing
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Sequence counter for Plant IDs — per-org, gapless, protected by advisory lock
    plant_id_sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Audit chain head for quick verification
    audit_chain_head_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    branches: Mapped[list[Branch]] = relationship("Branch", back_populates="organization")
    users: Mapped[list[User]] = relationship("User", back_populates="organization")

    __table_args__ = (
        Index("ix_organization_slug", "slug"),
        Index("ix_organization_status", "status"),
    )


# ── Branch ────────────────────────────────────────────────────────────────────
class Branch(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "branch"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    organization: Mapped[Organization] = relationship("Organization", back_populates="branches")
    members: Mapped[list[Membership]] = relationship("Membership", back_populates="branch")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_branch_org_code"),
        Index("ix_branch_organization_id", "organization_id"),
    )


# ── Role ──────────────────────────────────────────────────────────────────────
class Role(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "role"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)  # cannot be deleted

    permissions: Mapped[list[RolePermission]] = relationship("RolePermission", back_populates="role")
    memberships: Mapped[list[Membership]] = relationship("Membership", back_populates="role")

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_role_org_slug"),
        Index("ix_role_organization_id", "organization_id"),
        # RLS
        Index("ix_role_rls", "organization_id"),
    )


# ── Permission ────────────────────────────────────────────────────────────────
class Permission(Base, TimestampMixin):
    """Platform-defined permissions (seeded, not org-specific)."""

    __tablename__ = "permission"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permission"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    role: Mapped[Role] = relationship("Role", back_populates="permissions")
    permission: Mapped[Permission] = relationship("Permission")


# ── User ──────────────────────────────────────────────────────────────────────
class User(Base, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # NULL for SSO-only
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=UserStatus.PENDING_INVITE)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # TOTP
    totp_secret_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    backup_codes_hashed: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    # Brute-force protection
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Preferences
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    locale: Mapped[str] = mapped_column(String(10), default="en-IN")
    preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    # Invite
    invite_token_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    invite_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship("Organization", back_populates="users")
    memberships: Mapped[list[Membership]] = relationship("Membership", back_populates="user")
    sessions: Mapped[list[Session]] = relationship("Session", back_populates="user")

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_user_org_email"),
        Index("ix_user_organization_id", "organization_id"),
        Index("ix_user_email", "email"),
        Index("ix_user_status", "status"),
        # RLS
        Index("ix_user_rls", "organization_id"),
    )


# ── Membership (User ↔ Role ↔ Branch) ────────────────────────────────────────
class Membership(Base, TimestampMixin):
    """
    A user can have multiple memberships within an organization,
    each with a specific role, optionally scoped to a branch.
    """

    __tablename__ = "membership"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="RESTRICT"), nullable=False
    )
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branch.id", ondelete="SET NULL"), nullable=True
    )
    granted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="memberships")
    role: Mapped[Role] = relationship("Role", back_populates="memberships")
    branch: Mapped[Optional[Branch]] = relationship("Branch", back_populates="members")

    __table_args__ = (
        Index("ix_membership_organization_id", "organization_id"),
        Index("ix_membership_user_id", "user_id"),
        Index("ix_membership_role_id", "role_id"),
        Index("ix_membership_rls", "organization_id"),
    )


# ── Session ───────────────────────────────────────────────────────────────────
class Session(Base, TimestampMixin):
    __tablename__ = "user_session"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SessionStatus.ACTIVE)
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    totp_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("ix_session_user_id", "user_id"),
        Index("ix_session_refresh_token_hash", "refresh_token_hash"),
        Index("ix_session_status", "status"),
        Index("ix_session_rls", "organization_id"),
    )


# ── Device ────────────────────────────────────────────────────────────────────
class Device(Base, TimestampMixin):
    """Mobile / desktop device registration for session management."""

    __tablename__ = "device"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    device_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    trusted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "device_fingerprint", name="uq_device_user_fingerprint"),
        Index("ix_device_rls", "organization_id"),
    )


# ── API Key ───────────────────────────────────────────────────────────────────
class ApiKey(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # for display
    scopes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_api_key_hash", "key_hash"),
        Index("ix_api_key_rls", "organization_id"),
    )
