"""
Solar Operations OS — Core Configuration
All settings loaded from environment variables with validation.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    APP_NAME: str = "Solar Operations OS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = "postgresql://solar_user:solar_dev_password_123@localhost:5432/solar_operations"  # type: ignore[assignment]
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    # Separate URL for migrations (may use a privileged user)
    DATABASE_MIGRATION_URL: PostgresDsn | None = None
    # DB role that runs application queries (restricted — no superuser)
    DATABASE_APP_USER: str = "solar_app"
    DATABASE_APP_PASSWORD: str = ""

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"  # type: ignore[assignment]
    REDIS_MAX_CONNECTIONS: int = 20

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    JWT_PRIVATE_KEY_PEM: str = "dev_private_key"
    JWT_PUBLIC_KEY_PEM: str = "dev_public_key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_SECONDS: int = 900   # 15 minutes
    JWT_REFRESH_TOKEN_TTL_SECONDS: int = 604800  # 7 days
    JWT_ISSUER: str = "solar-ops-os"
    JWT_AUDIENCE: str = "solar-ops-os-api"

    # Argon2id parameters
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 2

    # ── Security ──────────────────────────────────────────────────────────────
    AUDIT_CHECKPOINT_HMAC_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    QR_SIGNING_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    FIELD_ENCRYPTION_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    SECRET_KEY: str = "dev_secret_key_32_bytes_minimum_length_required_for_signing_tokens"

    # ── Object Storage ────────────────────────────────────────────────────────
    S3_ENDPOINT_URL: AnyHttpUrl | None = None  # None = AWS; set for MinIO
    S3_BUCKET_DOCUMENTS: str = "solar-os-documents"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "ap-south-1"
    S3_SIGNED_URL_TTL_SECONDS: int = 900  # 15 minutes
    S3_DOWNLOAD_URL_TTL_SECONDS: int = 300  # 5 minutes

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_STANDARD_RPM: int = 1000
    RATE_LIMIT_AUTH_RPM: int = 10
    RATE_LIMIT_UPLOAD_RPM: int = 50
    RATE_LIMIT_IMPORT_RPM: int = 5
    RATE_LIMIT_COMPLIANCE_RPM: int = 10
    RATE_LIMIT_BRUTE_FORCE_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_BRUTE_FORCE_LOCKOUT_SECONDS: int = 1800  # 30 min

    # ── Async Workers ─────────────────────────────────────────────────────────
    WORKER_CONCURRENCY: int = 10
    OUTBOX_POLL_INTERVAL_SECONDS: float = 0.5
    OUTBOX_MAX_DELIVERY_ATTEMPTS: int = 5
    JOB_MAX_RETRIES: int = 3
    JOB_RETRY_DELAY_SECONDS: int = 60

    # ── Plant ID ──────────────────────────────────────────────────────────────
    # Format: SOL-{STATE_CODE}-{SEQUENCE:06d}
    # State code comes from organization.state_code
    PLANT_ID_PREFIX: str = "SOL"

    # ── Compliance Engine ─────────────────────────────────────────────────────
    COMPLIANCE_DEBOUNCE_SECONDS: int = 60
    COMPLIANCE_ENGINE_VERSION: str = "1.0.0"

    # ── Reconciliation Engine ─────────────────────────────────────────────────
    RECONCILIATION_DEBOUNCE_SECONDS: int = 30

    # ── Telemetry / Observability ─────────────────────────────────────────────
    OTEL_ENDPOINT: str | None = None  # OTLP gRPC endpoint
    PROMETHEUS_METRICS_PORT: int = 9090
    SENTRY_DSN: str | None = None

    # ── Feature Flags ─────────────────────────────────────────────────────────
    FEATURE_FLAG_DEFAULT_PLAN: str = "starter"

    # ── Document Intelligence (V2 seam) ───────────────────────────────────────
    AI_PROCESSING_ENABLED: bool = False  # off by default, org-level override
    AI_PROVIDER: Literal["openai", "gemini", "mock"] = "mock"
    AI_API_KEY: str = ""

    # ── Maintenance ───────────────────────────────────────────────────────────
    AUDIT_CHAIN_CHECKPOINT_INTERVAL_HOURS: int = 24
    RULE_FRESHNESS_WARN_DAYS: int = 90  # flag rules not reviewed in 90 days

    @field_validator("DATABASE_MIGRATION_URL", mode="before")
    @classmethod
    def default_migration_url(cls, v: str | None, info: object) -> str | None:
        """Fall back to DATABASE_URL if no separate migration URL is provided."""
        return v  # None means use DATABASE_URL in alembic.ini

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()  # type: ignore[call-arg]
