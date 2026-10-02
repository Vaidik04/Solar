"""
Solar Operations OS — Document Store & Verification: Database Models
Owns: DocumentType, Document, DocumentVersion, DocumentVerification, Certificate
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, SoftDeleteMixin, TenantMixin, TimestampMixin, VersionMixin


class DocCategory(StrEnum):
    CUSTOMER_KYC = "customer_kyc"
    PROPERTY_AND_ROOF = "property_and_roof"
    DISCOM_APPROVAL = "discom_approval"
    CEIG_APPROVAL = "ceig_approval"  # Chief Electrical Inspector to Govt
    ENGINEERING_DRAWING = "engineering_drawing"
    EQUIPMENT_DATASHEET = "equipment_datasheet"
    FACTORY_TEST_CERTIFICATE = "factory_test_certificate"
    WCR_REPORT = "wcr_report"
    NET_METER_TEST_REPORT = "net_meter_test_report"
    SAFETY_AND_EARTHING_REPORT = "safety_and_earthing_report"
    WARRANTY_CERTIFICATE = "warranty_certificate"
    INSURANCE_POLICY = "insurance_policy"
    SUBSIDY_APPLICATION = "subsidy_application"
    OTHER = "other"


class DocStatus(StrEnum):
    PENDING_UPLOAD = "pending_upload"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VerificationDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED_FOR_HUMAN_REVIEW = "flagged_for_human_review"


# ── Document Type ─────────────────────────────────────────────────────────────
class DocumentType(Base, TenantMixin, TimestampMixin, VersionMixin):
    __tablename__ = "document_type"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default=DocCategory.OTHER)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_mandatory_for_commissioning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validity_period_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allowed_mime_types: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), nullable=False, default=lambda: ["application/pdf", "image/jpeg", "image/png"]
    )
    max_file_size_mb: Mapped[int] = mapped_column(Integer, default=25, nullable=False)

    documents: Mapped[list[Document]] = relationship("Document", back_populates="document_type")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_doc_type_org_code"),
        Index("ix_doc_type_category", "organization_id", "category"),
    )


# ── Document ──────────────────────────────────────────────────────────────────
class Document(Base, TenantMixin, TimestampMixin, SoftDeleteMixin, VersionMixin):
    __tablename__ = "document"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=True
    )
    plant_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.id", ondelete="CASCADE"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DocStatus.PENDING_VERIFICATION)
    current_version_num: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    document_type: Mapped[DocumentType] = relationship("DocumentType", back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_document_project", "organization_id", "project_id"),
        Index("ix_document_plant", "organization_id", "plant_id"),
        Index("ix_document_status", "organization_id", "status"),
    )


# ── Document Version (Content-Addressed Storage) ──────────────────────────────
class DocumentVersion(Base, TenantMixin, TimestampMixin):
    __tablename__ = "document_version"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    uploaded_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    document: Mapped[Document] = relationship("Document", back_populates="versions")
    verifications: Mapped[list[DocumentVerification]] = relationship(
        "DocumentVerification", back_populates="version", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("document_id", "version_num", name="uq_doc_version_num"),
        Index("ix_doc_ver_sha256", "organization_id", "sha256_hash"),
    )


# ── Document Verification ─────────────────────────────────────────────────────
class DocumentVerification(Base, TenantMixin, TimestampMixin):
    __tablename__ = "document_verification"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False
    )
    verifier_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    version: Mapped[DocumentVersion] = relationship("DocumentVersion", back_populates="verifications")

    __table_args__ = (
        Index("ix_doc_verif_version", "version_id"),
    )


# ── Certificate (Formal Seals & Compliance Docs) ──────────────────────────────
class Certificate(Base, TenantMixin, TimestampMixin):
    __tablename__ = "certificate"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    plant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    certificate_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "CEIG_CHARGING_SAFETY", "DISCOM_NET_METERING"
    certificate_number: Mapped[str] = mapped_column(String(100), nullable=False)
    issuing_authority: Mapped[str] = mapped_column(String(255), nullable=False)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_cert_project", "organization_id", "project_id"),
        Index("ix_cert_plant", "organization_id", "plant_id"),
        Index("ix_cert_num", "organization_id", "certificate_number"),
    )
