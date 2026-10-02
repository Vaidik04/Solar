"""
Phase 10 Acceptance Tests:
1. Full offline job completed and synced across multiple entities.
2. Chaos resilience: duplicate packet retransmissions acknowledged idempotently.
3. Conflict resolution: server lock prevents illegal overwrite.
"""
from app.modules.field.sync_service import (
    OfflineSyncEngine,
    BatchSyncRequest,
    ClientMutation,
    MutationStatus,
)


def test_offline_job_sync_batch_success():
    """
    Acceptance: Full offline job completed (3 inspection checkpoints + 1 asset scan)
    and synced cleanly.
    """
    engine = OfflineSyncEngine()
    device_id = "ANDROID-TAB-TECH-04"

    mutations = [
        ClientMutation(
            mutation_id="mut-1",
            device_id=device_id,
            client_timestamp="2026-03-15T09:30:00Z",
            sequence_num=1,
            entity_type="inspection_item",
            entity_id="INSP-ITEM-EARTH",
            action="upsert",
            payload={"result": "pass", "earth_resistance_ohms": 2.4},
        ),
        ClientMutation(
            mutation_id="mut-2",
            device_id=device_id,
            client_timestamp="2026-03-15T09:35:00Z",
            sequence_num=2,
            entity_type="inspection_item",
            entity_id="INSP-ITEM-ISOLATOR",
            action="upsert",
            payload={"result": "pass", "trip_time_ms": 42},
        ),
        ClientMutation(
            mutation_id="mut-3",
            device_id=device_id,
            client_timestamp="2026-03-15T09:40:00Z",
            sequence_num=3,
            entity_type="asset_scan",
            entity_id="AST-INV-001",
            action="scan",
            payload={"serial": "SNG-2026-X88721", "qr_valid": True},
        ),
    ]

    req = BatchSyncRequest(
        device_id=device_id,
        last_synced_sequence=0,
        mutations=mutations,
    )

    resp = engine.process_sync_batch(req)
    assert resp.processed_count == 3
    assert resp.applied_count == 3
    assert resp.duplicate_count == 0
    assert resp.conflict_count == 0

    earth_state = engine.get_entity_state("INSP-ITEM-EARTH")
    assert earth_state is not None
    assert earth_state["data"]["earth_resistance_ohms"] == 2.4


def test_offline_sync_chaos_duplicate_replay_idempotence():
    """
    Acceptance: Network glitch causes device to resend batch -> server handles duplicate
    mutations idempotently without corrupting version counters.
    """
    engine = OfflineSyncEngine()
    device_id = "ANDROID-TAB-TECH-04"

    mut = ClientMutation(
        mutation_id="mut-fixed-101",
        device_id=device_id,
        client_timestamp="2026-03-15T10:00:00Z",
        sequence_num=1,
        entity_type="inspection_item",
        entity_id="INSP-ITEM-VOLT",
        action="upsert",
        payload={"voc_volts": 680.5},
    )

    req = BatchSyncRequest(
        device_id=device_id,
        last_synced_sequence=0,
        mutations=[mut],
    )

    # 1. First sync -> APPLIED
    resp1 = engine.process_sync_batch(req)
    assert resp1.applied_count == 1
    assert resp1.duplicate_count == 0

    # 2. Chaos retry -> DUPLICATE acknowledged
    resp2 = engine.process_sync_batch(req)
    assert resp2.applied_count == 0
    assert resp2.duplicate_count == 1
    assert resp2.items[0].status == MutationStatus.DUPLICATE


def test_offline_sync_conflict_on_locked_entity():
    """
    Acceptance: Offline mutation targeted at a locked entity results in CONFLICT status.
    """
    engine = OfflineSyncEngine()
    device_id = "ANDROID-TAB-TECH-04"

    # Seed locked state on server
    engine._entity_states["WCR-LOCKED-001"] = {
        "data": {"status": "approved"},
        "version": 3,
        "locked": True,
    }

    mut = ClientMutation(
        mutation_id="mut-illegal-override",
        device_id=device_id,
        client_timestamp="2026-03-15T10:15:00Z",
        sequence_num=1,
        entity_type="wcr",
        entity_id="WCR-LOCKED-001",
        action="upsert",
        payload={"capacity": 600.0},
    )

    req = BatchSyncRequest(device_id=device_id, last_synced_sequence=0, mutations=[mut])
    resp = engine.process_sync_batch(req)

    assert resp.conflict_count == 1
    assert resp.items[0].status == MutationStatus.CONFLICT
    assert "locked" in resp.items[0].message
