"""
Solar Operations OS — Documents Module: Domain Events
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from app.core.events import DomainEvent


@dataclass
class DocumentUploaded(DomainEvent):
    document_id: uuid.UUID = uuid.UUID(int=0)
    version_id: uuid.UUID = uuid.UUID(int=0)
    project_id: Optional[uuid.UUID] = None
    plant_id: Optional[str] = None
    doc_type_code: str = ""
    sha256_hash: str = ""


@dataclass
class DocumentVerified(DomainEvent):
    document_id: uuid.UUID = uuid.UUID(int=0)
    version_id: uuid.UUID = uuid.UUID(int=0)
    verifier_user_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    plant_id: Optional[str] = None


@dataclass
class DocumentRejected(DomainEvent):
    document_id: uuid.UUID = uuid.UUID(int=0)
    version_id: uuid.UUID = uuid.UUID(int=0)
    rejection_reason: str = ""


@dataclass
class CertificateIssued(DomainEvent):
    certificate_id: uuid.UUID = uuid.UUID(int=0)
    project_id: uuid.UUID = uuid.UUID(int=0)
    plant_id: str = ""
    certificate_type: str = ""
    certificate_number: str = ""
