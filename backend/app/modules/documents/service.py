"""
Solar Operations OS — Document Store Service
Implements content-addressed storage (ADR-007), cryptographic hashing,
versioning, and structured verification workflows.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.events import event_bus
from app.core.storage import get_storage_service
from app.modules.documents.events import (
    DocumentRejected,
    DocumentUploaded,
    DocumentVerified,
)
from app.modules.documents.models import (
    DocStatus,
    Document,
    DocumentType,
    DocumentVerification,
    DocumentVersion,
    VerificationDecision,
)
from app.modules.documents.public import (
    DocumentCreate,
    DocumentTypeCreate,
    DocumentVerificationCreate,
)
from app.modules.project.models import Project


class DocumentService:
    # ── Document Type ─────────────────────────────────────────────────────────
    async def create_document_type(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: DocumentTypeCreate,
    ) -> DocumentType:
        stmt = select(DocumentType).where(
            DocumentType.organization_id == org_id,
            DocumentType.code == data.code,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        doc_type = DocumentType(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            category=data.category,
            description=data.description,
            is_mandatory_for_commissioning=data.is_mandatory_for_commissioning,
            validity_period_months=data.validity_period_months,
            allowed_mime_types=data.allowed_mime_types,
            max_file_size_mb=data.max_file_size_mb,
        )
        session.add(doc_type)
        await session.flush()
        return doc_type

    # ── Document Lifecycle ───────────────────────────────────────────────────
    async def create_document(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        data: DocumentCreate,
    ) -> Document:
        plant_id = None
        if data.project_id:
            proj_stmt = select(Project.plant_id).where(
                Project.id == data.project_id,
                Project.organization_id == org_id,
            )
            plant_id = (await session.execute(proj_stmt)).scalar_one_or_none()

        doc = Document(
            organization_id=org_id,
            document_type_id=data.document_type_id,
            project_id=data.project_id,
            plant_id=plant_id,
            site_id=data.site_id,
            title=data.title,
            status=DocStatus.PENDING_VERIFICATION,
            current_version_num=1,
            expires_at=data.expires_at,
        )
        session.add(doc)
        await session.flush()
        return doc

    async def upload_version(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        document_id: uuid.UUID,
        uploader_user_id: Optional[uuid.UUID],
        file_bytes: bytes,
        filename: str,
        mime_type: str,
    ) -> DocumentVersion:
        doc = await self.get_document(session, org_id, document_id)

        # Content-addressed storage (ADR-007)
        storage = get_storage_service()
        content_hash, storage_key = storage.upload_bytes(
            organization_id=org_id,
            data=file_bytes,
            filename=filename,
            content_type=mime_type,
        )

        version_num = len(doc.versions) + 1 if doc.versions else 1
        doc.current_version_num = version_num
        doc.status = DocStatus.PENDING_VERIFICATION

        version = DocumentVersion(
            organization_id=org_id,
            document_id=doc.id,
            version_num=version_num,
            file_name=filename,
            storage_key=storage_key,
            sha256_hash=content_hash,
            file_size_bytes=len(file_bytes),
            mime_type=mime_type,
            uploaded_by_user_id=uploader_user_id,
            uploaded_at=datetime.now(timezone.utc),
        )
        session.add(version)
        await session.flush()

        await event_bus.emit_to_outbox(
            session,
            DocumentUploaded(
                organization_id=org_id,
                document_id=doc.id,
                version_id=version.id,
                project_id=doc.project_id,
                plant_id=doc.plant_id,
                doc_type_code=doc.document_type.code if doc.document_type else "",
                sha256_hash=content_hash,
            ),
        )
        return version

    async def verify_document(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        version_id: uuid.UUID,
        verifier_user_id: uuid.UUID,
        verification_data: DocumentVerificationCreate,
    ) -> DocumentVerification:
        # Load version and parent document
        ver_stmt = (
            select(DocumentVersion)
            .where(
                DocumentVersion.id == version_id,
                DocumentVersion.organization_id == org_id,
            )
            .options(selectinload(DocumentVersion.document))
        )
        version = (await session.execute(ver_stmt)).scalar_one_or_none()
        if not version:
            raise NotFoundError("DocumentVersion", str(version_id))

        doc = version.document
        now = datetime.now(timezone.utc)

        verification = DocumentVerification(
            organization_id=org_id,
            version_id=version.id,
            verifier_user_id=verifier_user_id,
            decision=verification_data.decision,
            verified_at=now,
            rejection_reason=verification_data.rejection_reason,
            extracted_fields=verification_data.extracted_fields,
        )
        session.add(verification)

        if verification_data.decision == VerificationDecision.APPROVED:
            doc.status = DocStatus.VERIFIED
            await event_bus.emit_to_outbox(
                session,
                DocumentVerified(
                    organization_id=org_id,
                    document_id=doc.id,
                    version_id=version.id,
                    verifier_user_id=verifier_user_id,
                    project_id=doc.project_id,
                    plant_id=doc.plant_id,
                ),
            )
        else:
            doc.status = DocStatus.REJECTED
            await event_bus.emit_to_outbox(
                session,
                DocumentRejected(
                    organization_id=org_id,
                    document_id=doc.id,
                    version_id=version.id,
                    rejection_reason=verification_data.rejection_reason or "Rejected by verifier",
                ),
            )

        await session.flush()
        return verification

    async def get_document(
        self,
        session: AsyncSession,
        org_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document:
        stmt = (
            select(Document)
            .where(
                Document.id == document_id,
                Document.organization_id == org_id,
                Document.deleted_at.is_(None),
            )
            .options(
                selectinload(Document.document_type),
                selectinload(Document.versions).selectinload(DocumentVersion.verifications),
            )
        )
        doc = (await session.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise NotFoundError("Document", str(document_id))
        return doc


document_service = DocumentService()
