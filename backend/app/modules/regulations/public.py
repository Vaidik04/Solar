"""
Solar Operations OS — Regulations Module: Public DTOs (Pydantic schemas)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Authority ─────────────────────────────────────────────────────────────────
class AuthorityCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    level: str = Field("state", max_length=50)
    state_code: Optional[str] = Field(None, max_length=10)
    website: Optional[str] = Field(None, max_length=512)


class AuthorityOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    level: str
    state_code: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Regulation ────────────────────────────────────────────────────────────────
class RegulationCreate(BaseModel):
    authority_id: uuid.UUID
    code: str = Field(..., max_length=100)
    title: str = Field(..., max_length=512)
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    is_active: bool = True
    applies_to_states: List[str] = Field(default_factory=list)


class RegulationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=512)
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    is_active: Optional[bool] = None
    applies_to_states: Optional[List[str]] = None


class RegulationOut(BaseModel):
    id: uuid.UUID
    authority_id: uuid.UUID
    code: str
    title: str
    description: Optional[str] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    is_active: bool
    applies_to_states: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Rule ──────────────────────────────────────────────────────────────────────
class RuleCreate(BaseModel):
    regulation_id: uuid.UUID
    code: str = Field(..., max_length=100)
    title: str = Field(..., max_length=512)
    rule_type: str = Field(..., max_length=50)
    status: str = Field("active", max_length=50)
    description: Optional[str] = None
    condition_dsl: Dict[str, Any] = Field(default_factory=dict)
    action_meta: Dict[str, Any] = Field(default_factory=dict)
    min_capacity_kw: Optional[str] = None
    max_capacity_kw: Optional[str] = None
    applies_to_system_types: List[str] = Field(default_factory=list)


class RuleUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=512)
    rule_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    condition_dsl: Optional[Dict[str, Any]] = None
    action_meta: Optional[Dict[str, Any]] = None
    min_capacity_kw: Optional[str] = None
    max_capacity_kw: Optional[str] = None
    applies_to_system_types: Optional[List[str]] = None


class RuleOut(BaseModel):
    id: uuid.UUID
    regulation_id: uuid.UUID
    code: str
    title: str
    rule_type: str
    status: str
    description: Optional[str] = None
    condition_dsl: Dict[str, Any]
    action_meta: Dict[str, Any]
    min_capacity_kw: Optional[str] = None
    max_capacity_kw: Optional[str] = None
    applies_to_system_types: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── RuleSet ───────────────────────────────────────────────────────────────────
class RuleSetCreate(BaseModel):
    code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    state_code: Optional[str] = Field(None, max_length=10)
    system_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    rule_ids: List[str] = Field(default_factory=list)


class RuleSetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    state_code: Optional[str] = None
    system_type: Optional[str] = None
    description: Optional[str] = None
    rule_ids: Optional[List[str]] = None


class RuleSetOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    state_code: Optional[str] = None
    system_type: Optional[str] = None
    description: Optional[str] = None
    rule_ids: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── DSL Evaluation Request/Response ───────────────────────────────────────────
class RuleEvaluationRequest(BaseModel):
    rule_id: uuid.UUID
    context: Dict[str, Any]


class RuleEvaluationResult(BaseModel):
    rule_id: uuid.UUID
    rule_code: str
    passed: bool
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)
