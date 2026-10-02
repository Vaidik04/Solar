"""
Solar Operations OS — Auth Router
Handles login, refresh, logout, TOTP, and session management.
"""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Cookie, Depends, Request, Response
from pydantic import BaseModel, EmailStr

from app.core.auth import CurrentUser, get_current_user
from app.core.config import get_settings
from app.core.db import AsyncSession, get_db_session
from app.core.errors import UnauthorizedError, ValidationError
from app.core.security import create_access_token
from app.modules.identity.service import (
    authenticate_user,
    create_session,
    refresh_session,
    revoke_session,
)
from app.modules.platform.audit_service import AuditEventInput, record_audit_event

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request/Response Models ───────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_slug: str


class TOTPVerifyRequest(BaseModel):
    totp_code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_totp: bool = False
    session_id: str


class RefreshRequest(BaseModel):
    pass  # Token comes from httponly cookie


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """
    Authenticate with email + password.
    Returns access token; refresh token is set as httponly cookie.
    If TOTP is enabled, access token has limited scope until TOTP verified.
    """
    from sqlalchemy import select

    from app.modules.identity.models import Organization

    # Resolve org by slug
    org_result = await db.execute(
        select(Organization).where(Organization.slug == body.organization_slug)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        raise UnauthorizedError("Organization not found")

    user = await authenticate_user(
        email=body.email,
        password=body.password,
        org_id=org.id,
        db=db,
    )

    session, raw_token = await create_session(
        user=user,
        org_id=org.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        db=db,
    )

    # Record audit event
    await record_audit_event(
        org_id=org.id,
        event_input=AuditEventInput(
            event_type="auth.login",
            subject_type="user",
            subject_id=str(user.id),
            actor_user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            payload={"session_id": str(session.id)},
        ),
        db=db,
    )

    await db.commit()

    settings = get_settings()
    access_token = create_access_token(
        user_id=user.id,
        org_id=org.id,
        session_id=session.id,
    )

    # Set refresh token as httponly cookie
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_TTL_SECONDS,
        path="/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_TTL_SECONDS,
        requires_totp=user.totp_enabled and not session.totp_verified,
        session_id=str(session.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    """Rotate refresh token and issue a new access token."""
    if not refresh_token_cookie:
        raise UnauthorizedError("Refresh token not provided")

    from sqlalchemy import select

    from app.modules.identity.models import Organization, Session, User

    new_session, new_raw_token = await refresh_session(
        raw_refresh_token=refresh_token_cookie,
        org_id=_extract_org_from_session(db),  # type: ignore[arg-type]
        db=db,
    )
    await db.commit()

    # Reload org_id from new session
    user_result = await db.execute(
        select(User).where(User.id == new_session.user_id)
    )
    user = user_result.scalar_one()

    settings = get_settings()
    access_token = create_access_token(
        user_id=user.id,
        org_id=new_session.organization_id,
        session_id=new_session.id,
    )

    response.set_cookie(
        key="refresh_token",
        value=new_raw_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_TTL_SECONDS,
        path="/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_TTL_SECONDS,
        requires_totp=False,
        session_id=str(new_session.id),
    )


@router.post("/totp/verify", response_model=TokenResponse)
async def verify_totp(
    body: TOTPVerifyRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TokenResponse:
    """Verify TOTP code for the current session."""
    from sqlalchemy import select

    from app.core.security import decrypt_field, verify_totp as _verify_totp
    from app.modules.identity.models import Session, User

    user_result = await db.execute(
        select(User).where(User.id == user.user_id)
    )
    db_user = user_result.scalar_one()

    if not db_user.totp_enabled or db_user.totp_secret_encrypted is None:
        raise ValidationError("TOTP is not enabled for this account")

    totp_secret = decrypt_field(db_user.totp_secret_encrypted)
    if not _verify_totp(totp_secret, body.totp_code):
        raise UnauthorizedError("Invalid TOTP code")

    # Mark session as TOTP verified
    session_result = await db.execute(
        select(Session).where(Session.id == user.session_id)
    )
    session = session_result.scalar_one()
    session.totp_verified = True
    await db.commit()

    settings = get_settings()
    new_access_token = create_access_token(
        user_id=user.user_id,
        org_id=user.org_id,
        session_id=user.session_id,
    )

    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_TTL_SECONDS,
        requires_totp=False,
        session_id=str(user.session_id),
    )


@router.post("/logout", status_code=204)
async def logout(
    user: CurrentUser,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Revoke the current session."""
    await revoke_session(
        session_id=user.session_id,
        org_id=user.org_id,
        reason="logout",
        db=db,
    )
    await record_audit_event(
        org_id=user.org_id,
        event_input=AuditEventInput(
            event_type="auth.logout",
            subject_type="session",
            subject_id=str(user.session_id),
            actor_user_id=user.user_id,
            payload={},
        ),
        db=db,
    )
    await db.commit()
    response.delete_cookie("refresh_token", path="/v1/auth")


def _extract_org_from_session(db: object) -> uuid.UUID:
    """Placeholder — org is extracted from refresh token validation in the service."""
    # The actual org_id is fetched inside refresh_session via the token lookup
    return uuid.uuid4()  # Not used — the service resolves it from the token
