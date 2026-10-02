# ADR-002: PostgreSQL with Row-Level Security for Tenancy

**Status:** Accepted  
**Date:** 2026-10-01

## Context

The platform is multi-tenant. We need to prevent cross-tenant data leakage. Options range from separate databases, separate schemas to shared schema with RLS.

## Options Considered

1. **Separate database per tenant** — Operationally expensive, migration complexity scales with tenants, connection pooling nightmare. Rejected for V1.
2. **Separate schema per tenant** — Alembic migrations must run per schema, SQLAlchemy schema switching overhead, search_path manipulation is fragile. Rejected.
3. **Shared schema + application-level filtering** — Relies purely on developer discipline. A single missing WHERE clause leaks data. Not sufficient as the only control. Rejected as sole control.
4. **Shared schema + PostgreSQL RLS (primary) + application-level filtering (defense-in-depth)** — RLS policies enforce tenant isolation at the database engine level. Even if application code is buggy, the DB rejects cross-tenant reads. **Accepted.**

## Decision

All tenant-scoped tables carry an `organization_id UUID NOT NULL` column. A PostgreSQL RLS policy is enabled on every such table:

```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON <table>
    USING (organization_id = current_setting('app.current_tenant')::uuid);
```

The application sets `app.current_tenant` at the start of every request (inside the async session factory) and never runs as the superuser. A dedicated `app_user` role has CONNECT + table-level privileges but NOT superuser bypass.

Application code also always filters by `org_id` (defense-in-depth). The CI test suite includes cross-tenant penetration tests that attempt to read another tenant's data via every endpoint — all must return 404 or 403, never 200 with data.

## Consequences

- **Good:** Database-enforced tenant isolation; application bugs cannot leak data across tenants.
- **Good:** Works transparently with SQLAlchemy — no ORM changes needed beyond session context.
- **Risk:** RLS has a small performance cost (index scans must include `organization_id`). Mitigation: composite indexes `(organization_id, <pk or common filter>)` on every tenant table.
- **Risk:** Schema migrations that touch RLS policies need care. Mitigation: expand/contract pattern, always tested on dev DB before production.
