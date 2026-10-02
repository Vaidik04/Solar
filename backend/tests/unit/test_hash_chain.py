import uuid
import pytest
from app.modules.platform.audit_service import (
    _compute_event_hash,
    _compute_checkpoint_hmac,
)


def test_initial_event_hash_computation():
    """First event has prev_hash=None and computes deterministic hash."""
    seq = 1
    event_type = "PlantCreated"
    actor_id = str(uuid.uuid4())
    subject_type = "Plant"
    subject_id = "SOL-MH-000001"
    payload = {"capacity_kw": 10.5, "installer": "SolarCorp"}

    hash1 = _compute_event_hash(
        sequence_num=seq,
        event_type=event_type,
        actor_user_id=actor_id,
        subject_type=subject_type,
        subject_id=subject_id,
        payload=payload,
        prev_hash=None,
    )

    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hex length

    # Repeat computation must yield identical hash (deterministic)
    hash2 = _compute_event_hash(
        sequence_num=seq,
        event_type=event_type,
        actor_user_id=actor_id,
        subject_type=subject_type,
        subject_id=subject_id,
        payload=payload,
        prev_hash=None,
    )
    assert hash1 == hash2


def test_hash_chain_linkage():
    """Second event incorporates the hash of the first event as prev_hash."""
    # Event 1
    hash1 = _compute_event_hash(
        sequence_num=1,
        event_type="PlantCreated",
        actor_user_id=None,
        subject_type="Plant",
        subject_id="SOL-MH-000001",
        payload={"capacity": 5.0},
        prev_hash=None,
    )

    # Event 2 chained to Event 1
    hash2 = _compute_event_hash(
        sequence_num=2,
        event_type="InspectionCompleted",
        actor_user_id=None,
        subject_type="Inspection",
        subject_id="INSP-123",
        payload={"result": "PASS"},
        prev_hash=hash1,
    )

    assert hash2 != hash1
    assert len(hash2) == 64


def test_tamper_detection_in_payload():
    """Altering payload alters the event hash, breaking the downstream chain."""
    hash1 = _compute_event_hash(
        sequence_num=1,
        event_type="WarrantyRegistered",
        actor_user_id=None,
        subject_type="Warranty",
        subject_id="WAR-001",
        payload={"years": 5},
        prev_hash=None,
    )

    # Malicious actor changes "years" from 5 to 25
    tampered_hash1 = _compute_event_hash(
        sequence_num=1,
        event_type="WarrantyRegistered",
        actor_user_id=None,
        subject_type="Warranty",
        subject_id="WAR-001",
        payload={"years": 25},
        prev_hash=None,
    )

    assert hash1 != tampered_hash1


def test_checkpoint_hmac_signing():
    """Checkpoint computes a valid HMAC-SHA256 signature using the secret key."""
    org_id = str(uuid.uuid4())
    sequence_num = 100
    chain_head = "a" * 64
    created_at = "2026-10-01T12:00:00Z"

    hmac_sig = _compute_checkpoint_hmac(
        org_id=org_id,
        sequence_num=sequence_num,
        chain_head_hash=chain_head,
        created_at=created_at,
    )

    assert isinstance(hmac_sig, str)
    assert len(hmac_sig) == 64

    # Verification: identical input yields identical signature
    hmac_sig_check = _compute_checkpoint_hmac(
        org_id=org_id,
        sequence_num=sequence_num,
        chain_head_hash=chain_head,
        created_at=created_at,
    )
    assert hmac_sig == hmac_sig_check
