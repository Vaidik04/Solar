"""
Solar Operations OS — Documents Module: API Router
"""
from __future__ import annotations

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_permission
from app.core.db import get_db_session
from app.core.policy import Permission, UserContext
from app.modules.documents.public import (
    DocumentCreate,
    DocumentRead,
    DocumentTypeCreate,
    DocumentTypeRead,
    DocumentVerificationCreate,
    DocumentVerificationRead,
    DocumentVersionRead,
)
from app.modules.documents.service import document_service

router = APIRouter(prefix="/documents", tags=["Documents & Verification"])


@router.post(
    "/types",
    response_model=DocumentTypeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DOCUMENTS_TYPE_MANAGE))],
)
async def create_document_type(
    data: DocumentTypeCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentTypeRead:
    doc_type = await document_service.create_document_type(session, user.org_id, data)
    await session.commit()
    return DocumentTypeRead.model_validate(doc_type)


@router.post(
    "",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DOCUMENTS_UPLOAD))],
)
async def create_document(
    data: DocumentCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentRead:
    doc = await document_service.create_document(session, user.org_id, data)
    await session.commit()
    return DocumentRead.model_validate(doc)


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    dependencies=[Depends(require_permission(Permission.DOCUMENTS_READ))],
)
async def get_document(
    document_id: uuid.UUID,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentRead:
    doc = await document_service.get_document(session, user.org_id, document_id)
    return DocumentRead.model_validate(doc)


@router.post(
    "/{document_id}/upload",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DOCUMENTS_UPLOAD))],
)
async def upload_document_version(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    user: Annotated[UserContext, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> DocumentVersionRead:
    file_bytes = await file.read()
    version = await document_service.upload_version(
        session=session,
        org_id=user.org_id,
        document_id=document_id,
        uploader_user_id=user.user_id,
        file_bytes=file_bytes,
        filename=file.filename or "document.pdf",
        mime_type=file.content_type or "application/pdf",
    )
    await session.commit()
    return DocumentVersionRead.model_validate(version)


@router.post(
    "/versions/{version_id}/verify",
    response_model=DocumentVerificationRead,
    dependencies=[Depends(require_permission(Permission.DOCUMENTS_VERIFY))],
)
async def verify_document_version(
    version_id: uuid.UUID,
    data: DocumentVerificationCreate,
    user: Annotated[UserContext, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentVerificationRead:
    verification = await document_service.verify_document(
        session=session,
        org_id=user.org_id,
        version_id=version_id,
        verifier_user_id=user.user_id,
        verification_data=data,
    )
    await session.commit()
    return DocumentVerificationRead.model_validate(verification)
