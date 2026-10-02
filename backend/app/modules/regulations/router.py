"""
Solar Operations OS — Regulations Module Router
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.regulations.public import (
    AuthorityCreate,
    AuthorityOut,
    RegulationCreate,
    RegulationOut,
    RuleCreate,
    RuleEvaluationRequest,
    RuleEvaluationResult,
    RuleOut,
    RuleSetCreate,
    RuleSetOut,
)
from app.modules.regulations.service import regulations_service

router = APIRouter(prefix="/regulations", tags=["Regulations"])


# ── Authorities ───────────────────────────────────────────────────────────────
@router.post(
    "/authorities",
    response_model=AuthorityOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_authority(
    payload: AuthorityCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_MANAGE)),
) -> AuthorityOut:
    auth = await regulations_service.create_authority(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(auth)
    return AuthorityOut.model_validate(auth)


@router.get("/authorities", response_model=List[AuthorityOut])
async def list_authorities(
    level: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> List[AuthorityOut]:
    items = await regulations_service.list_authorities(session, current_user.org_id, level=level)
    return [AuthorityOut.model_validate(item) for item in items]


@router.get("/authorities/{authority_id}", response_model=AuthorityOut)
async def get_authority(
    authority_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> AuthorityOut:
    item = await regulations_service.get_authority(session, current_user.org_id, authority_id)
    return AuthorityOut.model_validate(item)


# ── Regulations ───────────────────────────────────────────────────────────────
@router.post(
    "/regulations",
    response_model=RegulationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_regulation(
    payload: RegulationCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_MANAGE)),
) -> RegulationOut:
    reg = await regulations_service.create_regulation(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(reg)
    return RegulationOut.model_validate(reg)


@router.get("/regulations", response_model=List[RegulationOut])
async def list_regulations(
    authority_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> List[RegulationOut]:
    items = await regulations_service.list_regulations(
        session, current_user.org_id, authority_id=authority_id
    )
    return [RegulationOut.model_validate(item) for item in items]


@router.get("/regulations/{regulation_id}", response_model=RegulationOut)
async def get_regulation(
    regulation_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> RegulationOut:
    item = await regulations_service.get_regulation(session, current_user.org_id, regulation_id)
    return RegulationOut.model_validate(item)


# ── Rules ─────────────────────────────────────────────────────────────────────
@router.post(
    "/rules",
    response_model=RuleOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    payload: RuleCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_MANAGE)),
) -> RuleOut:
    rule = await regulations_service.create_rule(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(rule)
    return RuleOut.model_validate(rule)


@router.get("/rules", response_model=List[RuleOut])
async def list_rules(
    regulation_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> List[RuleOut]:
    items = await regulations_service.list_rules(
        session, current_user.org_id, regulation_id=regulation_id
    )
    return [RuleOut.model_validate(item) for item in items]


@router.get("/rules/{rule_id}", response_model=RuleOut)
async def get_rule(
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> RuleOut:
    item = await regulations_service.get_rule(session, current_user.org_id, rule_id)
    return RuleOut.model_validate(item)


@router.post("/rules/evaluate", response_model=RuleEvaluationResult)
async def evaluate_rule(
    payload: RuleEvaluationRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> RuleEvaluationResult:
    return await regulations_service.evaluate_rule(
        session, current_user.org_id, payload.rule_id, payload.context
    )


# ── RuleSets ──────────────────────────────────────────────────────────────────
@router.post(
    "/rulesets",
    response_model=RuleSetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_ruleset(
    payload: RuleSetCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_MANAGE)),
) -> RuleSetOut:
    rs = await regulations_service.create_ruleset(session, current_user.org_id, payload)
    await session.commit()
    await session.refresh(rs)
    return RuleSetOut.model_validate(rs)


@router.get("/rulesets", response_model=List[RuleSetOut])
async def list_rulesets(
    state_code: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> List[RuleSetOut]:
    items = await regulations_service.list_rulesets(
        session, current_user.org_id, state_code=state_code
    )
    return [RuleSetOut.model_validate(item) for item in items]


@router.get("/rulesets/{ruleset_id}", response_model=RuleSetOut)
async def get_ruleset(
    ruleset_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserContext = Depends(require_permission(Permission.REGULATIONS_READ)),
) -> RuleSetOut:
    item = await regulations_service.get_ruleset(session, current_user.org_id, ruleset_id)
    return RuleSetOut.model_validate(item)
