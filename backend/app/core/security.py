"""
Solar Operations OS — Security Layer
JWT signing/verification, password hashing, TOTP, QR token signing.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.errors import UnauthorizedError

# ── Password Hashing ──────────────────────────────────────────────────────────
_pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,
    argon2__memory_cost=65536,
    argon2__parallelism=2,
)


def hash_password(plain: str) -> str:
    """Hash a password with argon2id."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its argon2id hash."""
    return _pwd_context.verify(plain, hashed)


def needs_rehash(hashed: str) -> bool:
    """True if the hash needs to be updated (e.g., cost parameters changed)."""
    return _pwd_context.needs_update(hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────
TokenType = Literal["access", "refresh_hint"]


def create_access_token(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    session_id: uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a short-lived RS256 access token."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org": str(org_id),
        "sid": str(session_id),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(seconds=settings.JWT_ACCESS_TOKEN_TTL_SECONDS),
        "type": "access",
        **(extra_claims or {}),
    }
    return jwt.encode(
        payload,
        settings.JWT_PRIVATE_KEY_PEM,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Verify and decode an access token.
    Raises UnauthorizedError on any failure.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY_PEM,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")
        return payload  # type: ignore[return-value]
    except JWTError as exc:
        raise UnauthorizedError(f"Invalid or expired token: {exc}") from exc


# ── Refresh Tokens ────────────────────────────────────────────────────────────
def generate_refresh_token() -> tuple[str, str]:
    """
    Generate a refresh token.
    Returns (raw_token, hashed_token).
    raw_token is sent to the client (once, in a httponly cookie).
    hashed_token is stored in the database.
    """
    raw = secrets.token_urlsafe(48)  # 360 bits of entropy
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── API Keys ──────────────────────────────────────────────────────────────────
def generate_api_key() -> tuple[str, str]:
    """
    Generate an API key.
    Returns (raw_key, hashed_key).
    Format: solar_{random_base62_48chars}
    """
    raw = f"solar_{secrets.token_urlsafe(36)}"
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── TOTP ──────────────────────────────────────────────────────────────────────
def generate_totp_secret() -> str:
    """Generate a TOTP secret (base32-encoded, 160 bits)."""
    import pyotp

    return pyotp.random_base32()


def verify_totp(secret: str, token: str, window: int = 1) -> bool:
    """Verify a TOTP token. Window allows 1 step drift (30s)."""
    import pyotp

    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=window)


def get_totp_provisioning_uri(secret: str, user_email: str) -> str:
    import pyotp

    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=user_email, issuer_name="Solar Operations OS"
    )


# ── QR Token Signing ──────────────────────────────────────────────────────────
def sign_qr_token(asset_id: uuid.UUID, org_id: uuid.UUID) -> str:
    """
    Create a signed opaque QR token for an asset.
    Format: base64url(asset_id_bytes || org_id_bytes || hmac)
    The token is opaque — it does not reveal the asset ID to unauthenticated users.
    """
    import base64

    settings = get_settings()
    key = bytes.fromhex(settings.QR_SIGNING_KEY)
    payload = asset_id.bytes + org_id.bytes  # 32 bytes
    mac = hmac.new(key, payload, hashlib.sha256).digest()
    token_bytes = payload + mac  # 64 bytes total
    return base64.urlsafe_b64encode(token_bytes).decode().rstrip("=")


def verify_qr_token(token: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    """
    Verify a QR token and extract (asset_id, org_id).
    Returns None if invalid or tampered.
    """
    import base64

    settings = get_settings()
    key = bytes.fromhex(settings.QR_SIGNING_KEY)
    try:
        # Restore padding
        padded = token + "=" * (4 - len(token) % 4)
        token_bytes = base64.urlsafe_b64decode(padded)
        if len(token_bytes) != 64:
            return None
        payload = token_bytes[:32]
        provided_mac = token_bytes[32:]
        expected_mac = hmac.new(key, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(provided_mac, expected_mac):
            return None
        asset_id = uuid.UUID(bytes=payload[:16])
        org_id = uuid.UUID(bytes=payload[16:32])
        return asset_id, org_id
    except Exception:
        return None


# ── Field-Level Encryption ────────────────────────────────────────────────────
def encrypt_field(plaintext: str) -> str:
    """Encrypt a sensitive field value (e.g., consumer number) with Fernet."""
    from cryptography.fernet import Fernet

    settings = get_settings()
    # Fernet key must be 32 url-safe base64-encoded bytes
    key_bytes = bytes.fromhex(settings.FIELD_ENCRYPTION_KEY)
    import base64

    fernet_key = base64.urlsafe_b64encode(key_bytes)
    f = Fernet(fernet_key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a field-level encrypted value."""
    from cryptography.fernet import Fernet, InvalidToken

    settings = get_settings()
    import base64

    key_bytes = bytes.fromhex(settings.FIELD_ENCRYPTION_KEY)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    f = Fernet(fernet_key)
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Field decryption failed — invalid ciphertext or key") from exc


# ── Content Hashing ───────────────────────────────────────────────────────────
def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_stream(chunks: list[bytes]) -> str:
    """Compute SHA-256 from streaming chunks."""
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


# ── Secure Random ─────────────────────────────────────────────────────────────
def generate_backup_codes(count: int = 10) -> list[str]:
    """Generate one-time backup codes for TOTP recovery."""
    return [secrets.token_hex(5).upper() for _ in range(count)]
