# ADR-003: Transactional Outbox for Domain Events

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Domain events (state transitions, reconciliation triggers, audit, search indexing, notifications) must be delivered reliably. In-process event publication fails if the process crashes after committing the state change but before publishing to a message broker. We cannot use two-phase commit.

## Decision

**Transactional Outbox Pattern.**

Every state-changing operation that produces domain events writes both the state change and the `OutboxEvent` rows in the **same database transaction**. A background worker (ARQ job) polls the outbox, delivers events to handlers (in-process fan-out for co-located modules, Redis pub-sub or direct handler call for async work), and marks events as delivered. Events are idempotent by `event_id` — handlers must be idempotent.

```
outbox_event table:
  id           UUID PK
  organization_id UUID
  event_type   TEXT
  payload      JSONB
  status       ENUM(pending, delivered, failed, dead)
  created_at   TIMESTAMPTZ
  deliver_after TIMESTAMPTZ (for delayed events)
  attempts     INT
  last_error   TEXT
  delivered_at TIMESTAMPTZ
```

Dead-letter: after N attempts, status → `dead`, alert fires, manual replay available.

## Alternatives Considered

- **Synchronous in-process events only** — Lost on crash. No retry. Rejected.
- **Kafka/RabbitMQ directly** — Adds infra dependency; at V1 scale Redis + outbox is sufficient. Clean seam to replace the dispatcher later. Rejected for V1.

## Consequences

- **Good:** Exactly-once delivery semantics achievable (at-least-once + idempotent handlers).
- **Good:** Events queryable in Postgres for debugging without a separate broker.
- **Risk:** Outbox polling adds DB load. Mitigation: short-poll interval (500ms) with SKIP LOCKED, dedicated outbox worker.
