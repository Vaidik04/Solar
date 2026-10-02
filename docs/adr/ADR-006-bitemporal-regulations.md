# ADR-006: Bitemporal Regulation and Rules Storage

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Compliance rules are time-sensitive in two independent dimensions:
1. **Valid time (VT):** When did this regulation actually apply in the real world? (effective_from / effective_until)
2. **Record time (RT):** When did we learn about / record this in our system? (recorded_at / superseded_at)

The system must answer: "What rules applied to project P on date D, as we knew it at time T?" This is required for reproducing past compliance runs and for audit.

## Decision

**Bitemporal tables for `regulation_version` and `rule_version`.**

```sql
regulation_version:
  id              UUID
  regulation_id   UUID FK
  content         JSONB        -- full snapshot of regulation text/reference
  valid_from      DATE NOT NULL -- VT start: when this version became law
  valid_until     DATE         -- VT end: NULL = currently effective
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()  -- RT start
  superseded_at   TIMESTAMPTZ -- RT end: NULL = currently our best knowledge
  recorded_by     UUID FK user
  source_url      TEXT
  notes           TEXT
```

Query helper:
```sql
-- Rules valid on date D, as known at time T
SELECT * FROM rule_version
WHERE valid_from <= :D
  AND (valid_until IS NULL OR valid_until > :D)   -- VT filter
  AND recorded_at <= :T
  AND (superseded_at IS NULL OR superseded_at > :T) -- RT filter
```

`ComplianceRun` stores `rules_snapshot JSONB` (full copies of rule versions used) so runs are self-contained regardless of subsequent regulation changes.

## Alternatives Considered

- **Single valid-time only** — Cannot reproduce "what did we know at time T". Rejected.
- **Event-sourced regulation changes** — More complex, no tooling advantage at this scale.

## Consequences

- **Good:** Full time-travel queries for compliance reproduction.
- **Good:** Audit of regulation knowledge changes (who recorded what, when).
- **Risk:** Bitemporal queries are complex. Mitigation: dedicated query helper functions in `regulations.service`; do not write raw bitemporal SQL in other modules.
