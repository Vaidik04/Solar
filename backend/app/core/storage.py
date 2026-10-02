"""
Solar Operations OS — Content-Addressed Storage Client (ADR-007)
Provides:
- Content-hash computation (SHA-256)
- Storage key layout: {organization_id}/{hash[:2]}/{hash[2:4]}/{hash}.{ext}
- Pre-signed upload & download URLs
- MinIO / S3 compatible client
"""
from __future__ import annotations

import hashlib
import uuid
from typing import BinaryIO, Optional

import boto3
from botocore.client import Config
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )

    @staticmethod
    def compute_sha256(data: bytes | BinaryIO) -> str:
        """Computes SHA-256 hash of byte sequence or file-like object."""
        hasher = hashlib.sha256()
        if isinstance(data, bytes):
            hasher.update(data)
        else:
            data.seek(0)
            while chunk := data.read(65536):
                hasher.update(chunk)
            data.seek(0)
        return hasher.hexdigest()

    def build_object_key(self, organization_id: uuid.UUID, content_hash: str, filename: str) -> str:
        """
        Content-addressed object path:
        {tenant_id}/{first_2_chars}/{next_2_chars}/{full_sha256}_{filename}
        Prevents S3 directory prefix hotspots and enforces tenant boundary.
        """
        prefix1 = content_hash[:2]
        prefix2 = content_hash[2:4]
        safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
        return f"{organization_id}/{prefix1}/{prefix2}/{content_hash}_{safe_name}"

    def upload_bytes(
        self,
        organization_id: uuid.UUID,
        data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> tuple[str, str]:
        """
        Uploads bytes directly to storage.
        Returns (content_hash, object_key).
        """
        content_hash = self.compute_sha256(data)
        key = self.build_object_key(organization_id, content_hash, filename)

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata={
                "sha256": content_hash,
                "organization-id": str(organization_id),
            },
        )
        logger.info(
            "file_uploaded",
            key=key,
            sha256=content_hash,
            bytes_size=len(data),
            organization_id=str(organization_id),
        )
        return content_hash, key

    def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600,
        content_disposition: Optional[str] = None,
    ) -> str:
        """Generates pre-signed GET URL with bounded expiration."""
        params = {"Bucket": self.bucket, "Key": key}
        if content_disposition:
            params["ResponseContentDisposition"] = content_disposition

        url: str = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return url

    def generate_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = 900,
    ) -> str:
        """Generates pre-signed PUT URL with content-type restriction."""
        url: str = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return url


_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
