# Solar Operations OS — API Conventions

**Version:** 1.0  
**Date:** 2026-10-01

---

## Base URL

```
https://api.solar-os.example.com/v1/
```

All paths below are relative to this base.

---

## Versioning

- API versioned by path prefix (`/v1/`).
- Breaking changes require a new version prefix.
- Non-breaking additions (new optional fields, new endpoints) do not require a new version.
- The `X-API-Version` response header echoes the current engine version.

---

## Authentication

```
Authorization: Bearer <access_token>
```

- Access tokens: JWT, 15-minute TTL, RS256 signed.
- Refresh tokens: opaque 256-bit random, stored as argon2id hash, 7-day TTL, single-use (rotated on refresh).
- API Keys: `X-API-Key: <key>` header, 256-bit random, stored as argon2id hash.
- TOTP: POST /auth/totp/verify after initial login challenge.

---

## Tenant Context

The tenant is determined exclusively from the authenticated user's organization membership. It **cannot** be overridden via headers or query parameters. Cross-org requests are rejected.

---

## Idempotency

All POST/PUT/PATCH endpoints that perform mutations accept:

```
Idempotency-Key: <client-generated UUID v4>
```

If the same key is presented within 24 hours, the original response is returned without re-executing the mutation. The response includes:

```
Idempotency-Replayed: true
```

Idempotency keys are **required** for:
- Workflow transitions
- Asset registration / bulk import
- Document upload
- Any endpoint tagged `mobile-mutation` in the OpenAPI spec

---

## Optimistic Concurrency

Editable aggregates return:

```
ETag: "version-<version_number>"
```

Update/patch requests for these resources **must** include:

```
If-Match: "version-<version_number>"
```

Mismatch → `409 Conflict` with body:

```json
{
  "type": "https://errors.solar-os.example.com/optimistic-concurrency",
  "title": "Concurrent modification conflict",
  "status": 409,
  "current_version": 42,
  "provided_version": 41
}
```

---

## Error Responses — RFC 7807 Problem Details

All errors use `Content-Type: application/problem+json`:

```json
{
  "type": "https://errors.solar-os.example.com/<error-code>",
  "title": "Human-readable title",
  "status": 422,
  "detail": "Specific description of this occurrence",
  "instance": "/v1/projects/abc-123/transition",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "errors": [
    {
      "field": "target_stage",
      "code": "invalid_transition",
      "message": "Cannot transition from DESIGN to COMMISSIONED"
    }
  ]
}
```

Never expose stack traces, internal table names, or SQL errors in production.

Error code registry (partial):

| HTTP | type suffix | Meaning |
|------|------------|---------|
| 400 | bad-request | Malformed input |
| 401 | unauthenticated | Missing/invalid token |
| 403 | forbidden | Authenticated but not authorized |
| 404 | not-found | Resource not found (or hidden by RLS) |
| 409 | optimistic-concurrency | ETag mismatch |
| 409 | duplicate-idempotency | Same idempotency key, different payload |
| 409 | state-conflict | Invalid state machine transition |
| 413 | payload-too-large | File exceeds size limit |
| 422 | validation-error | Schema/business validation failure |
| 429 | rate-limited | Too many requests |
| 503 | service-unavailable | Dependency unavailable |

---

## Pagination — Cursor-Based

```
GET /v1/projects?limit=50&cursor=<opaque_cursor>&sort=created_at:desc
```

Response envelope:

```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "next_cursor": "<opaque>",
    "prev_cursor": "<opaque>",
    "has_next": true,
    "has_prev": false,
    "total_count": 1234
  }
}
```

- Default limit: 50. Max limit: 200.
- Cursors are base64-encoded position markers (keyset pagination), not offsets.
- `total_count` is approximate (using PostgreSQL's `reltuples`) for large result sets; exact count available via `?exact_count=true` (capped at 10,000).

---

## Filtering and Sorting

Standard query parameters:

```
?filter[stage]=in:DESIGN,BOM
?filter[created_at]=gte:2024-01-01
?filter[customer_id]=eq:uuid-here
?sort=created_at:desc,plant_id:asc
?search=MNRE rooftop
```

Filters are AND-combined by default. OR within a field via `in:`. Operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains` (for text, triggers trigram), `is_null`, `is_not_null`.

---

## Request / Response Conventions

- All timestamps: ISO 8601 UTC (`2024-03-15T09:30:00Z`). Display as IST in the UI.
- All monetary values: integer paise (INR × 100). No floating-point money.
- All capacities: decimal `kWp`, stored as `NUMERIC(10,3)` in DB.
- All GPS: `{"lat": 28.6139, "lon": 77.2090, "accuracy_m": 5.0}`.
- All durations: ISO 8601 duration strings (`P30D`, `PT2H`).
- Soft-deleted resources: excluded from list responses by default; accessible via `?include_deleted=true` with `archival:read` permission.
- Effective-dated resources: default to `as_of=now()`; override with `?as_of=2024-01-01`.

---

## Bloom — Common Response Fields

All entity responses include:

```json
{
  "id": "uuid",
  "organization_id": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "version": 1,
  "created_by": "uuid",
  "updated_by": "uuid",
  "deleted_at": null
}
```

---

## Async Operations

Long-running operations (bulk import, compliance run, PDF generation, export) return:

```json
{
  "job_id": "uuid",
  "status": "queued",
  "poll_url": "/v1/jobs/uuid",
  "estimated_seconds": 30
}
```

Poll `GET /v1/jobs/{job_id}` for status. Completed jobs include `result_url` or inline `result`.

---

## OpenAPI Contract

The OpenAPI spec (`openapi.json`) is the **source of truth** for the API contract. It is:
- Generated from FastAPI routes and Pydantic models
- Committed to the repository on every CI run
- Used to generate the TypeScript client (`@solar-os/api-client`)
- Used in contract tests against both the web and mobile clients

Tags in OpenAPI: `auth`, `identity`, `crm`, `project`, `workflow`, `assets`, `supply`, `documents`, `regulations`, `compliance`, `reconciliation`, `field`, `warranty`, `oam`, `telemetry`, `platform`, `admin`

---

## Rate Limiting

Response headers on all endpoints:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1711363200
```

Default limits (per org, per minute):
- Standard endpoints: 1000 req/min
- Auth endpoints: 10 req/min
- Bulk import: 5 req/min
- File upload: 50 req/min
- Compliance run: 10 req/min

Exceeded: `429 Too Many Requests` with `Retry-After` header.

---

## Health and Observability Endpoints

```
GET /health       → 200 {"status": "ok"}  (liveness)
GET /ready        → 200 {"status": "ready", "checks": {...}}  (readiness — DB, Redis, S3)
GET /metrics      → Prometheus exposition format (internal network only)
```
