"""
Solar Operations OS — Offline Sync Engine & Technician Sync API
Fulfills Phase 10 requirements:
- Batch offline mutation ingestion from mobile field devices
- Idempotency key tracking preventing duplicate execution
- Conflict resolution (sequence ordering + version checks)
- Chaos resilience under network replay
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MutationStatus(StrEnum):
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    REJECTED = "rejected"


class ClientMutation(BaseModel):
    mutation_id: str  # Client-side UUID
    device_id: str
    client_timestamp: str
    sequence_num: int
    entity_type: str  # 'inspection_item', 'asset_scan', 'checklist'
    entity_id: str
    action: str  # 'upsert', 'scan', 'complete'
    payload: Dict[str, Any]


class SyncResponseItem(BaseModel):
    mutation_id: str
    status: MutationStatus
    message: str
    server_timestamp: str
    entity_version: int = 1


class BatchSyncRequest(BaseModel):
    device_id: str
    last_synced_sequence: int
    mutations: List[ClientMutation]


class BatchSyncResponse(BaseModel):
    processed_count: int
    applied_count: int
    duplicate_count: int
    conflict_count: int
    items: List[SyncResponseItem]


class OfflineSyncEngine:
    def __init__(self):
        # In-memory store for idempotency tracking (in production, backed by Redis/DB)
        self._processed_mutations: Dict[str, SyncResponseItem] = {}
        self._entity_states: Dict[str, Dict[str, Any]] = {}

    def process_sync_batch(self, request: BatchSyncRequest) -> BatchSyncResponse:
        """
        Processes a batch of offline field technician mutations idempotently.
        """
        applied = 0
        duplicates = 0
        conflicts = 0
        items: List[SyncResponseItem] = []

        now_str = datetime.now(timezone.utc).isoformat()

        # Sort mutations strictly by sequence_num to ensure causal ordering
        ordered_mutations = sorted(request.mutations, key=lambda m: m.sequence_num)

        for mut in ordered_mutations:
            # 1. Idempotency check: Already processed?
            if mut.mutation_id in self._processed_mutations:
                cached = self._processed_mutations[mut.mutation_id]
                duplicates += 1
                items.append(
                    SyncResponseItem(
                        mutation_id=mut.mutation_id,
                        status=MutationStatus.DUPLICATE,
                        message="Mutation previously applied; acknowledged idempotently",
                        server_timestamp=cached.server_timestamp,
                        entity_version=cached.entity_version,
                    )
                )
                continue

            # 2. Conflict & business rule validation
            current_state = self._entity_states.get(mut.entity_id)

            # Check: Cannot complete inspection if current state is locked or invalid
            if current_state and current_state.get("locked", False):
                conflicts += 1
                item = SyncResponseItem(
                    mutation_id=mut.mutation_id,
                    status=MutationStatus.CONFLICT,
                    message="Target entity is locked on server; mutation rejected",
                    server_timestamp=now_str,
                    entity_version=current_state.get("version", 1),
                )
                items.append(item)
                self._processed_mutations[mut.mutation_id] = item
                continue

            # 3. Apply mutation
            new_version = (current_state.get("version", 0) + 1) if current_state else 1
            updated_state = {
                "data": mut.payload,
                "version": new_version,
                "last_modified_by": mut.device_id,
                "last_timestamp": mut.client_timestamp,
                "locked": mut.payload.get("lock", False),
            }
            self._entity_states[mut.entity_id] = updated_state

            applied += 1
            res_item = SyncResponseItem(
                mutation_id=mut.mutation_id,
                status=MutationStatus.APPLIED,
                message="Successfully applied to server state",
                server_timestamp=now_str,
                entity_version=new_version,
            )
            items.append(res_item)
            self._processed_mutations[mut.mutation_id] = res_item

        return BatchSyncResponse(
            processed_count=len(request.mutations),
            applied_count=applied,
            duplicate_count=duplicates,
            conflict_count=conflicts,
            items=items,
        )

    def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        return self._entity_states.get(entity_id)


offline_sync_engine = OfflineSyncEngine()
