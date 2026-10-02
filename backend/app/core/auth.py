"""
Solar Operations OS — FastAPI Auth Dependencies
Provides get_current_user, require_permission, and related dependencies.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.db import get_db_session, set_current_tenant_id
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.policy import AuthzResource, UserContext, policy_engine
from app.core.security import verify_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


# ── Extract and Verify Token ──────────────────────────────────────────────────
async def _get_token_payload(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict:
    """
    Extract JWT payload from Bearer token or validate API key.
    Returns the token payload dict.
    """
    if credentials is not None:
        return verify_access_token(credentials.credentials)

    if x_api_key is not None:
        # API key validation — delegated to identity module at runtime
        # (Circular import avoided by lazy import)
        from app.modules.identity.service import validate_api_key_and_build_payload

        payload = await validate_api_key_and_build_payload(x_api_key)
        if payload is None:
            raise UnauthorizedError("Invalid API key")
        return payload

    raise UnauthorizedError("Authentication required")


# ── Build UserContext from DB ─────────────────────────────────────────────────
async def get_current_user(
    payload: Annotated[dict, Depends(_get_token_payload)],
    session: Annotated[object, Depends(get_db_session)],
) -> UserContext:
    """
    Load the full UserContext for the authenticated user.
    Sets the tenant context variable for RLS.
    This dependency is used on every protected endpoint.
    """
    try:
        user_id = uuid.UUID(payload["sub"])
        org_id = uuid.UUID(payload["org"])
        session_id = uuid.UUID(payload["sid"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token claims") from exc

    # Set tenant context FIRST — this activates RLS for all subsequent queries
    set_current_tenant_id(org_id)

    # Load user with permissions from DB (identity module)
    from app.modules.identity.service import load_user_context

    user_ctx = await load_user_context(
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        db=session,  # type: ignore[arg-type]
    )
    if user_ctx is None:
        raise UnauthorizedError("User not found or deactivated")

    return user_ctx


# ── Permission Check Dependency Factory ──────────────────────────────────────
def require_permission(
    permission: str,
    resource_factory: object | None = None,
) -> object:
    """
    FastAPI dependency factory for permission checks.

    Usage:
        @router.get("/projects")
        async def list_projects(
            user: Annotated[UserContext, Depends(require_permission("project:read"))]
        ):
            ...
    """

    async def _check(
        user: Annotated[UserContext, Depends(get_current_user)],
        request: Request,
    ) -> UserContext:
        # Build a basic resource from the user's org context
        # Endpoints that need fine-grained ABAC build AuthzResource themselves
        resource = AuthzResource(org_id=user.org_id)
        result = policy_engine.authorize(user, permission, resource)
        if not result.allowed:
            raise ForbiddenError(result.reason)
        return user

    return _check


# ── Typed Dependency Aliases ──────────────────────────────────────────────────
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
