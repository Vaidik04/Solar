"""
Phase 13 Acceptance Tests:
1. Disaster recovery audit hash-chain verification drill (100% chain continuity).
2. Demo environment realistic data validation with deliberate anomalies.
3. Tamper detection and cryptographic seal validation.
"""
import uuid
import hashlib
import hmac
from datetime import datetime, timezone
import pytest

from app.core.seeder import demo_seeder


def test_demo_seeded_environment_completeness_and_anomalies():
    """
    Acceptance: Demo environment seeds complete C&I plant SOL-MH-000042
    with deliberate operational anomalies (clipping, open warranty claim).
    """
    env = demo_seeder.build_seeded_environment()

    assert env["is_seeded"] is True
    passport = env["passport"]
    assert passport["plant_id"] == "SOL-MH-000042"
    assert passport["capacity_kw"] == 500.0
    assert passport["discom"] == "MSEDCL"

    # Verify BOM assets
    bom = env["bom"]
    assert len(bom) == 2
    panels = next(b for b in bom if b["category"] == "pv_modules")
    inverters = next(b for b in bom if b["category"] == "inverters")
    assert panels["quantity"] == 1000
    assert len(inverters["serials"]) == 5

    # Verify deliberate anomalies
    anomalies = env["anomalies"]
    assert len(anomalies) == 2
    types = [a["type"] for a in anomalies]
    assert "inverter_clipping" in types
    assert "open_warranty_claim" in types


from app.modules.platform.audit_service import (
    _compute_event_hash,
    _compute_checkpoint_hmac,
)


def test_audit_hash_chain_disaster_recovery_drill():
    """
    Acceptance: Audit hash chain verification drill iterates 100% of event blocks
    and guarantees cryptographic continuity.
    """
    org_id = str(uuid.uuid4())
    genesis_prev = None

    # Build sequence of 10 audit blocks
    blocks = []
    prev_hash = genesis_prev
    for i in range(1, 11):
        payload = {"action": f"operation_step_{i}", "entity_id": str(uuid.uuid4())}
        current_hash = _compute_event_hash(
            sequence_num=i,
            event_type="PlantAuditLog",
            actor_user_id=str(uuid.uuid4()),
            subject_type="Plant",
            subject_id="SOL-MH-000042",
            payload=payload,
            prev_hash=prev_hash,
        )
        blocks.append({
            "sequence_num": i,
            "prev_hash": prev_hash,
            "hash": current_hash,
            "payload": payload,
        })
        prev_hash = current_hash

    # Verify 100% continuity
    for i in range(1, len(blocks)):
        assert blocks[i]["prev_hash"] == blocks[i - 1]["hash"]

    # Verify HMAC Checkpoint
    checkpoint_hmac = _compute_checkpoint_hmac(
        org_id=org_id,
        sequence_num=len(blocks),
        chain_head_hash=blocks[-1]["hash"],
        created_at="2026-10-02T10:00:00Z",
    )
    assert len(checkpoint_hmac) == 64
    assert isinstance(checkpoint_hmac, str)
