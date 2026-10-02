"""
Solar Operations OS — Documents Public Schemas (DTOs)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.modules.documents.models import DocCategory, DocStatus, VerificationDecision


# ── Document Type DTOs ────────────────────────────────────────────────────────
class DocumentTypeBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    category: DocCategory = DocCategory.OTHER
    description: Optional[str] = None
    is_mandatory_for_commissioning: bool = False
    validity_period_months: Optional[int] = None
    allowed_mime_types: List[str] = Field(default_factory=lambda: ["application/pdf", "image/jpeg", "image/png"])
    max_file_size_mb: int = Field(25, ge=1, le=100)


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeRead(DocumentTypeBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Document Verification DTOs ────────────────────────────────────────────────
class DocumentVerificationCreate(BaseModel):
    decision: VerificationDecision
    rejection_reason: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)


class DocumentVerificationRead(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    verifier_user_id: Optional[uuid.UUID] = None
    decision: VerificationDecision
    verified_at: datetime
    rejection_reason: Optional[str] = None
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ── Document Version DTOs ─────────────────────────────────────────────────────
class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_num: int
    file_name: str
    storage_key: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    uploaded_by_user_id: Optional[uuid.UUID] = None
    uploaded_at: datetime
    verifications: List[DocumentVerificationRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ── Document DTOs ─────────────────────────────────────────────────────────────
class DocumentCreate(BaseModel):
    document_type_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    site_id: Optional[uuid.UUID] = None
    title: str = Field(..., min_length=2, max_length=255)
    expires_at: Optional[datetime] = None


class DocumentRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    document_type_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    plant_id: Optional[str] = None
    site_id: Optional[uuid.UUID] = None
    title: str
    status: DocStatus
    current_version_num: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    versions: List[DocumentVersionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
