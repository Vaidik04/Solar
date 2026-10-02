import uuid
from app.core.idempotency import _hash_payload, _make_redis_key


def test_hash_payload_deterministic():
    payload_a = {"capacity_kw": 12.0, "notes": "Phase 1 roof array"}
    payload_b = {"notes": "Phase 1 roof array", "capacity_kw": 12.0}

    # Keys are sorted, so order of dict keys does not affect hash
    assert _hash_payload(payload_a) == _hash_payload(payload_b)


def test_hash_payload_changes_on_difference():
    payload_a = {"capacity_kw": 12.0}
    payload_b = {"capacity_kw": 12.1}

    assert _hash_payload(payload_a) != _hash_payload(payload_b)


def test_make_redis_key_scoped_by_tenant():
    org_1 = uuid.uuid4()
    org_2 = uuid.uuid4()
    key = "idem-req-123"

    redis_key_1 = _make_redis_key(org_1, key)
    redis_key_2 = _make_redis_key(org_2, key)

    assert str(org_1) in redis_key_1
    assert str(org_2) in redis_key_2
    assert redis_key_1 != redis_key_2
