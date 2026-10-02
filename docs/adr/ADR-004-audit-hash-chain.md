# ADR-004: Audit Hash Chain for Tamper Evidence

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Audit events must be tamper-evident. Simply logging to a table is insufficient — rows can be deleted or modified. We need a mechanism to detect tampering without requiring external infrastructure.

## Decision

**Per-tenant append-only hash chain in PostgreSQL.**

```
audit_event:
  id            BIGSERIAL (gapless per tenant enforced by sequence)
  organization_id UUID
  sequence_num  BIGINT NOT NULL  -- gapless per tenant
  event_type    TEXT
  actor_user_id UUID
  subject_type  TEXT
  subject_id    UUID
  payload       JSONB
  ip_address    INET
  user_agent    TEXT
  event_hash    TEXT  -- SHA-256(sequence_num || event_type || actor || subject || payload || prev_hash)
  prev_hash     TEXT  -- hash of previous event in this tenant's chain (NULL for first)
  created_at    TIMESTAMPTZ
```

Database enforcement:
```sql
REVOKE UPDATE, DELETE ON audit_event FROM app_user;
-- Only INSERT is permitted
```

A **verification job** runs on demand and on schedule:
- Reads events in sequence order per tenant
- Recomputes each hash and checks it matches stored hash
- Verifies chain linkage (each prev_hash matches the hash of the prior record)
- Reports first tampered event, gap in sequence, or broken link

**Checkpoint anchoring:** Periodically (e.g., daily) a signed checkpoint is written (`audit_checkpoint` table) storing the current chain head hash, sequence number, and a HMAC signed with a key stored in the secret manager. This provides a "witness" that cannot be backdated even if the database is restored from backup.

## Alternatives Considered

- **External audit log service** — Adds dependency, latency, and complexity. The hash chain provides sufficient tamper evidence for V1 at zero infra cost.
- **Blockchain / merkle tree** — Overkill for V1. The hash chain design is compatible with upgrading to a merkle tree later.

## Consequences

- **Good:** Any deletion or modification of an audit record is detectable.
- **Good:** Gap detection (sequence numbers must be contiguous per tenant).
- **Risk:** If `prev_hash` is known, an attacker with DB access could reconstruct a valid chain. Mitigation: checkpoints signed with off-DB key; for V1 this is acceptable.
- **Risk:** High audit volume creates a hot sequence. Mitigation: sequence is per-tenant (low per-tenant volume), BRIN index on created_at.
