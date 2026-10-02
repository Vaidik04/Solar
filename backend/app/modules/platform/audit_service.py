"""
Solar Operations OS — Audit Service
Implements the append-only hash chain (ADR-004).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.platform.models import AuditCheckpoint, AuditEvent

logger = structlog.get_logger()


# ── Hash Chain ────────────────────────────────────────────────────────────────
def _compute_event_hash(
    sequence_num: int,
    event_type: str,
    actor_user_id: str | None,
    subject_type: str,
    subject_id: str | None,
    payload: dict[str, Any],
    prev_hash: str | None,
) -> str:
    """
    Deterministic SHA-256 hash of an audit event.
    Input: canonical JSON of all event fields + prev_hash.
    """
    canonical = json.dumps(
        {
            "sequence_num": sequence_num,
            "event_type": event_type,
            "actor_user_id": actor_user_id,
            "subject_type": subject_type,
            "subject_id": subject_id,
            "payload": payload,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _compute_checkpoint_hmac(
    org_id: str,
    sequence_num: int,
    chain_head_hash: str,
    created_at: str,
) -> str:
    """HMAC-SHA256 of checkpoint data, signed with the off-DB key."""
    settings = get_settings()
    key = bytes.fromhex(settings.AUDIT_CHECKPOINT_HMAC_KEY)
    message = json.dumps(
        {
            "org_id": org_id,
            "sequence_num": sequence_num,
            "chain_head_hash": chain_head_hash,
            "created_at": created_at,
        },
        sort_keys=True,
    ).encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


# ── Audit Service ─────────────────────────────────────────────────────────────
@dataclass
class AuditEventInput:
    event_type: str
    subject_type: str
    payload: dict[str, Any]
    actor_user_id: uuid.UUID | None = None
    actor_api_key_id: uuid.UUID | None = None
    subject_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass
class ChainVerificationResult:
    verified: bool
    events_checked: int
    first_failure_sequence: int | None
    failure_reason: str | None


async def record_audit_event(
    org_id: uuid.UUID,
    event_input: AuditEventInput,
    db: AsyncSession,
) -> AuditEvent:
    """
    Append an audit event to the hash chain.

    Uses PostgreSQL advisory lock to ensure sequence_num is gapless per org.
    Must be called within an existing transaction.
    """
    # Advisory lock per organization to serialize sequence assignment
    # Lock key: hash of org_id (org_id is a UUID, convert to a 64-bit int)
    lock_key = int(org_id.int % (2**63))
    await db.execute(text(f"SELECT pg_advisory_xact_lock({lock_key})"))

    # Get current max sequence for this org
    result = await db.execute(
        select(func.max(AuditEvent.sequence_num)).where(
            AuditEvent.organization_id == org_id
        )
    )
    current_max: int | None = result.scalar()
    next_seq = (current_max or 0) + 1

    # Get previous hash
    prev_hash: str | None = None
    if current_max is not None:
        prev_result = await db.execute(
            select(AuditEvent.event_hash).where(
                AuditEvent.organization_id == org_id,
                AuditEvent.sequence_num == current_max,
            )
        )
        prev_hash = prev_result.scalar()

    # Compute hash
    event_hash = _compute_event_hash(
        sequence_num=next_seq,
        event_type=event_input.event_type,
        actor_user_id=str(event_input.actor_user_id) if event_input.actor_user_id else None,
        subject_type=event_input.subject_type,
        subject_id=event_input.subject_id,
        payload=event_input.payload,
        prev_hash=prev_hash,
    )

    now = datetime.now(timezone.utc)
    event = AuditEvent(
        id=uuid.uuid4(),
        organization_id=org_id,
        sequence_num=next_seq,
        event_type=event_input.event_type,
        actor_user_id=event_input.actor_user_id,
        actor_api_key_id=event_input.actor_api_key_id,
        subject_type=event_input.subject_type,
        subject_id=event_input.subject_id,
        payload=event_input.payload,
        ip_address=event_input.ip_address,
        user_agent=event_input.user_agent,
        event_hash=event_hash,
        prev_hash=prev_hash,
        created_at=now,
    )
    db.add(event)
    logger.debug(
        "audit_event_recorded",
        org_id=str(org_id),
        event_type=event_input.event_type,
        sequence_num=next_seq,
    )
    return event


async def verify_audit_chain(
    org_id: uuid.UUID,
    db: AsyncSession,
    from_seq: int = 1,
    to_seq: int | None = None,
) -> ChainVerificationResult:
    """
    Verify the audit hash chain for an organization.

    Reads events in sequence order and:
    1. Recomputes each hash and compares to stored hash
    2. Verifies chain linkage (prev_hash matches previous event's hash)
    3. Checks sequence numbers are contiguous
    """
    query = (
        select(AuditEvent)
        .where(AuditEvent.organization_id == org_id)
        .where(AuditEvent.sequence_num >= from_seq)
        .order_by(AuditEvent.sequence_num)
    )
    if to_seq is not None:
        query = query.where(AuditEvent.sequence_num <= to_seq)

    result = await db.execute(query)
    events = result.scalars().all()

    if not events:
        return ChainVerificationResult(
            verified=True, events_checked=0, first_failure_sequence=None, failure_reason=None
        )

    prev_hash: str | None = None
    expected_seq = from_seq

    for event in events:
        # 1. Sequence continuity
        if event.sequence_num != expected_seq:
            return ChainVerificationResult(
                verified=False,
                events_checked=expected_seq - from_seq,
                first_failure_sequence=expected_seq,
                failure_reason=f"Gap in sequence: expected {expected_seq}, found {event.sequence_num}",
            )

        # 2. Chain linkage
        if event.sequence_num == from_seq and from_seq == 1:
            if event.prev_hash is not None:
                return ChainVerificationResult(
                    verified=False,
                    events_checked=0,
                    first_failure_sequence=event.sequence_num,
                    failure_reason="First event must have NULL prev_hash",
                )
        elif event.prev_hash != prev_hash:
            return ChainVerificationResult(
                verified=False,
                events_checked=event.sequence_num - from_seq,
                first_failure_sequence=event.sequence_num,
                failure_reason=(
                    f"Chain break at sequence {event.sequence_num}: "
                    f"expected prev_hash={prev_hash}, got={event.prev_hash}"
                ),
            )

        # 3. Hash integrity
        computed = _compute_event_hash(
            sequence_num=event.sequence_num,
            event_type=event.event_type,
            actor_user_id=str(event.actor_user_id) if event.actor_user_id else None,
            subject_type=event.subject_type,
            subject_id=event.subject_id,
            payload=event.payload,
            prev_hash=event.prev_hash,
        )
        if computed != event.event_hash:
            return ChainVerificationResult(
                verified=False,
                events_checked=event.sequence_num - from_seq,
                first_failure_sequence=event.sequence_num,
                failure_reason=(
                    f"Hash mismatch at sequence {event.sequence_num}: "
                    f"stored={event.event_hash}, computed={computed}"
                ),
            )

        prev_hash = event.event_hash
        expected_seq += 1

    return ChainVerificationResult(
        verified=True,
        events_checked=len(events),
        first_failure_sequence=None,
        failure_reason=None,
    )


async def create_checkpoint(org_id: uuid.UUID, db: AsyncSession) -> AuditCheckpoint:
    """
    Create a signed checkpoint anchoring the current chain head.
    Called periodically by the background worker.
    """
    settings = get_settings()

    # Get current chain head
    result = await db.execute(
        select(AuditEvent.sequence_num, AuditEvent.event_hash)
        .where(AuditEvent.organization_id == org_id)
        .order_by(AuditEvent.sequence_num.desc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        raise ValueError(f"No audit events found for org {org_id}")

    sequence_num, chain_head_hash = row
    now = datetime.now(timezone.utc)
    created_at_str = now.isoformat()

    hmac_sig = _compute_checkpoint_hmac(
        org_id=str(org_id),
        sequence_num=sequence_num,
        chain_head_hash=chain_head_hash,
        created_at=created_at_str,
    )

    checkpoint = AuditCheckpoint(
        id=uuid.uuid4(),
        organization_id=org_id,
        sequence_num=sequence_num,
        chain_head_hash=chain_head_hash,
        hmac_signature=hmac_sig,
        created_at=now,
        engine_version=settings.APP_VERSION,
    )
    db.add(checkpoint)
    logger.info(
        "audit_checkpoint_created",
        org_id=str(org_id),
        sequence_num=sequence_num,
        chain_head_hash=chain_head_hash,
    )
    return checkpoint


async def verify_checkpoint(
    checkpoint: AuditCheckpoint,
) -> bool:
    """Verify a checkpoint's HMAC signature."""
    expected = _compute_checkpoint_hmac(
        org_id=str(checkpoint.organization_id),
        sequence_num=checkpoint.sequence_num,
        chain_head_hash=checkpoint.chain_head_hash,
        created_at=checkpoint.created_at.isoformat(),
    )
    return hmac.compare_digest(expected, checkpoint.hmac_signature)
