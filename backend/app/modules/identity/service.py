"""
Solar Operations OS — Identity Module Service
Provides: user loading, permission resolution, session management, API key validation.
This is the ONLY module that reads role/permission/membership tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError, UnauthorizedError, ValidationError
from app.core.policy import UserContext
from app.core.security import (
    generate_refresh_token,
    hash_api_key,
    hash_refresh_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.modules.identity.models import (
    ApiKey,
    Membership,
    Organization,
    Role,
    RolePermission,
    Session,
    SessionStatus,
    User,
    UserStatus,
    Permission,
)

logger = structlog.get_logger()


# ── User Context Loading ──────────────────────────────────────────────────────
async def load_user_context(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession,
) -> UserContext | None:
    """
    Load the full UserContext for request processing.
    Resolves all roles → permissions for this user in this org.
    """
    # Load user with memberships eagerly
    result = await db.execute(
        select(User)
        .where(
            User.id == user_id,
            User.organization_id == org_id,
            User.deleted_at.is_(None),
        )
        .options(
            selectinload(User.memberships).selectinload(Membership.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission)
        )
    )
    user = result.scalar_one_or_none()
    if user is None or user.status not in (UserStatus.ACTIVE,):
        return None

    # Load session
    sess_result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.status == SessionStatus.ACTIVE,
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    session = sess_result.scalar_one_or_none()
    if session is None:
        return None

    # Resolve permissions from active memberships
    permissions: set[str] = set()
    branch_ids: set[uuid.UUID] = set()

    for membership in user.memberships:
        if membership.revoked_at is not None:
            continue
        if membership.branch_id is not None:
            branch_ids.add(membership.branch_id)
        for rp in membership.role.permissions:
            permissions.add(rp.permission.code)

    # Load org plan
    org_result = await db.execute(
        select(Organization.plan).where(Organization.id == org_id)
    )
    plan = org_result.scalar() or "starter"

    return UserContext(
        user_id=user.id,
        org_id=org_id,
        session_id=session_id,
        email=user.email,
        is_active=True,
        is_platform_admin=user.is_platform_admin,
        permissions=permissions,
        branch_ids=branch_ids,
        assigned_project_ids=set(),  # Loaded lazily when needed
        plan=plan,
        totp_verified=session.totp_verified,
    )


# ── Authentication ────────────────────────────────────────────────────────────
async def authenticate_user(
    email: str,
    password: str,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> User:
    """
    Verify email/password and return the User.
    Handles brute-force lockout.
    """
    from app.core.config import get_settings

    settings = get_settings()

    result = await db.execute(
        select(User).where(
            User.email == email.lower().strip(),
            User.organization_id == org_id,
            User.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    # Timing-safe: always do password check even if user not found
    dummy_hash = "$argon2id$v=19$m=65536,t=2,p=2$invalid"

    if user is None:
        verify_password(password, dummy_hash)  # constant-time
        raise UnauthorizedError("Invalid email or password")

    # Check lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise UnauthorizedError(
            f"Account locked until {user.locked_until.isoformat()}. Too many failed attempts."
        )

    if user.status == UserStatus.INACTIVE:
        raise UnauthorizedError("Account is deactivated")

    if user.password_hash is None:
        raise UnauthorizedError("Password login not enabled for this account (use SSO)")

    if not verify_password(password, user.password_hash):
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.RATE_LIMIT_BRUTE_FORCE_MAX_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                seconds=settings.RATE_LIMIT_BRUTE_FORCE_LOCKOUT_SECONDS
            )
            user.status = UserStatus.LOCKED
            logger.warning("user_locked_brute_force", user_id=str(user.id))
        await db.commit()
        raise UnauthorizedError("Invalid email or password")

    # Success — reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    if user.status == UserStatus.LOCKED:
        user.status = UserStatus.ACTIVE
    user.last_login_at = datetime.now(timezone.utc)

    # Rehash if needed (cost parameters changed)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    return user


# ── Session Management ────────────────────────────────────────────────────────
async def create_session(
    user: User,
    org_id: uuid.UUID,
    ip_address: str | None,
    user_agent: str | None,
    db: AsyncSession,
) -> tuple[Session, str]:
    """
    Create a new session and return (Session, raw_refresh_token).
    The raw refresh token is sent to the client; the hash is stored.
    """
    from app.core.config import get_settings

    settings = get_settings()
    raw_token, hashed_token = generate_refresh_token()

    session = Session(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user.id,
        refresh_token_hash=hashed_token,
        status=SessionStatus.ACTIVE,
        ip_address=ip_address,
        user_agent=user_agent,
        totp_verified=False,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=settings.JWT_REFRESH_TOKEN_TTL_SECONDS),
        last_used_at=datetime.now(timezone.utc),
    )
    db.add(session)
    return session, raw_token


async def refresh_session(
    raw_refresh_token: str,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> tuple[Session, str]:
    """
    Rotate a refresh token: revoke old, issue new.
    Returns (new_session, new_raw_token).
    """
    hashed = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(Session).where(
            Session.refresh_token_hash == hashed,
            Session.organization_id == org_id,
            Session.status == SessionStatus.ACTIVE,
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    old_session = result.scalar_one_or_none()
    if old_session is None:
        raise UnauthorizedError("Invalid or expired refresh token")

    # Revoke old session
    old_session.status = SessionStatus.REVOKED
    old_session.revoked_at = datetime.now(timezone.utc)
    old_session.revoked_reason = "rotated"

    # Load user for new session
    user_result = await db.execute(
        select(User).where(User.id == old_session.user_id)
    )
    user = user_result.scalar_one()

    return await create_session(
        user=user,
        org_id=org_id,
        ip_address=old_session.ip_address,
        user_agent=old_session.user_agent,
        db=db,
    )


async def revoke_session(
    session_id: uuid.UUID,
    org_id: uuid.UUID,
    reason: str,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.organization_id == org_id,
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.status = SessionStatus.REVOKED
        session.revoked_at = datetime.now(timezone.utc)
        session.revoked_reason = reason


# ── API Key Validation ────────────────────────────────────────────────────────
async def validate_api_key_and_build_payload(raw_key: str) -> dict | None:
    """
    Validate an API key and build a JWT-equivalent payload dict.
    Called from core.auth (lazy import to avoid circular dependency).
    """
    from app.core.db import get_session_factory

    hashed = hash_api_key(raw_key)
    factory = get_session_factory()

    async with factory() as db:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == hashed,
                ApiKey.deleted_at.is_(None),
                (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > datetime.now(timezone.utc)),
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return None

        # Update last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        await db.commit()

        return {
            "sub": str(api_key.user_id),
            "org": str(api_key.organization_id),
            "sid": str(uuid.uuid4()),  # virtual session for API key
            "type": "access",
            "scopes": api_key.scopes,
        }
