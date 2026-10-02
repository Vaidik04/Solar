import uuid
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    generate_api_key,
    hash_api_key,
    generate_totp_secret,
    verify_totp,
    sign_qr_token,
    verify_qr_token,
    encrypt_field,
    decrypt_field,
    compute_sha256,
)


def test_password_hash_and_verify():
    password = "SuperSecretPassword#2026!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_api_key_generation_and_hashing():
    raw_key, hashed_key = generate_api_key()
    assert raw_key.startswith("solar_")
    assert len(hashed_key) == 64
    assert hash_api_key(raw_key) == hashed_key


def test_totp_generation_and_verification():
    import pyotp

    secret = generate_totp_secret()
    assert len(secret) == 32
    totp = pyotp.TOTP(secret)
    current_token = totp.now()

    assert verify_totp(secret, current_token) is True
    assert verify_totp(secret, "000000") is False


def test_qr_token_signing_and_verification():
    asset_id = uuid.uuid4()
    org_id = uuid.uuid4()

    token = sign_qr_token(asset_id, org_id)
    assert isinstance(token, str)

    extracted = verify_qr_token(token)
    assert extracted is not None
    extracted_asset_id, extracted_org_id = extracted
    assert extracted_asset_id == asset_id
    assert extracted_org_id == org_id

    # Tampered token fails verification
    tampered = ("A" if token[0] != "A" else "B") + token[1:]
    assert verify_qr_token(tampered) is None


def test_field_encryption_roundtrip():
    sensitive = "DISCOM_CONSUMER_NO_987654321"
    encrypted = encrypt_field(sensitive)
    assert encrypted != sensitive
    decrypted = decrypt_field(encrypted)
    assert decrypted == sensitive


def test_compute_sha256():
    data = b"solar operations passport test data"
    digest = compute_sha256(data)
    assert len(digest) == 64
    assert compute_sha256(data) == digest
