# Solar Operations OS — Threat Model (STRIDE)

**Date:** 2026-10-01  
**Scope:** Phase 0 — to be updated at each major phase.

---

## Assets and Trust Boundaries

### Assets to Protect
1. Tenant data (projects, assets, documents, customers) — primary business data
2. Audit chain — tamper evidence
3. Document blobs — customer and regulatory documents
4. Authentication credentials (passwords, tokens, API keys, TOTP secrets)
5. Encryption keys and secrets
6. Serial numbers and asset identity
7. Compliance run results

### Trust Boundaries
- **TB1:** Public internet → API Gateway (TLS termination)
- **TB2:** API Gateway → FastAPI application
- **TB3:** FastAPI → PostgreSQL (private network, app_user role, RLS active)
- **TB4:** FastAPI → MinIO/S3 (private network, signed requests)
- **TB5:** FastAPI → Redis (private network, password-protected)
- **TB6:** Admin UI → FastAPI (same as TB1/TB2 but admin role)
- **TB7:** Mobile client → API (same as TB1/TB2, plus offline sync endpoints)
- **TB8:** FastAPI → External inverter APIs (egress, credential vault)
- **TB9:** FastAPI → External AI/OCR providers (egress, PII redaction required)

---

## STRIDE Analysis

### S — Spoofing

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| JWT token theft | Auth | Short-lived access tokens (15 min), rotating refresh tokens (7 days), rotation on use | Token replay after rotation returns 401 |
| Session fixation | Auth | New session ID on login | Automated session test |
| API key brute-force | Auth | Keys are 256-bit random, stored as argon2id hash, never in logs | N/A |
| QR token spoofing | Assets | QR payloads are HMAC-signed opaque tokens, not raw IDs | Invalid signature → 404 |
| Cross-tenant impersonation | RLS | `app.current_tenant` set from authenticated user's org, never from request body | Cross-tenant test suite |
| TOTP bypass | Auth | TOTP enforced when enabled per org; backup codes are single-use | Rate limit on TOTP attempts |

### T — Tampering

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| Audit log modification | Audit | REVOKE UPDATE/DELETE on audit_event; hash chain | Tamper detection test modifies row, chain verify fails |
| Document blob modification | Storage | Content-addressed (SHA-256), hash stored in DB; re-verification fails if blob is replaced | Hash mismatch test |
| Rule version tampering | Regulations | Compliance runs store full rule snapshot; version is immutable after publish | Rule modification after publish → new version required |
| Serial number manipulation | Assets | Import is transactional; asset events are append-only; impossible states enforced by DB constraints | Constraint violation tests |
| Request body tampering in transit | Transport | TLS 1.3 enforced; HSTS | N/A |
| Optimistic concurrency bypass | Aggregates | ETag / version column on editable aggregates; mismatch → 409 | Concurrent edit test |

### R — Repudiation

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| User denies action | Audit | Every mutating action writes to audit_event with actor, IP, user-agent, timestamp, payload | Audit event present after every mutation in integration tests |
| Workflow override without reason | Workflow | Override requires `reason` (mandatory field) + elevated permission; recorded in stage_history | Override without reason → 422 |
| AI assistant action repudiation | AI (V2) | Every AI-initiated mutation requires explicit user confirmation; confirmation event in audit | N/A Phase 0 |

### I — Information Disclosure

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| Cross-tenant data leak | RLS | RLS policy active; app-level org_id filter; cross-tenant penetration tests | Cross-tenant test suite (Phase 1 acceptance) |
| Enumeration via predictable IDs | API | UUIDs for internal IDs; Plant IDs (SOL-MP-000124) reveal org+sequence but not other tenants | Sequential scan test returns only own org's data |
| Document URL leakage | Storage | Signed URLs (15 min TTL); org prefix in storage key | Expired URL returns 403 |
| Verbose error messages | API | RFC 7807 problem details with codes, not stack traces, in production | Error response schema test |
| Secrets in logs | Logging | Structured logging config excludes `password`, `token`, `secret`, `key` fields | Log scrubbing test |
| PII in AI prompts | AI (V2) | PII redaction hook before any external AI call; org-level data-processing consent flag | N/A Phase 0 |
| Consumer numbers / sensitive fields | DB | Field-level encryption for consumer_number, aadhaar-linked fields | Encryption at-rest test |

### D — Denial of Service

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| Bulk import flooding | Assets | Rate limit on import endpoint; max batch size 10k; streaming parse with memory cap | Rate limit test |
| Large file upload | Storage | Max file size enforced at API gateway (50MB) before content reaches app | Oversized upload → 413 |
| Expensive compliance re-runs | Compliance | Debounce: one run per project per 60s; runs are async (job queue) | Rapid trigger test produces one run |
| Login brute force | Auth | 5 failed attempts → 30-min lockout with exponential backoff; CAPTCHA seam | Brute-force lockout test |
| Dashboard query DoS | Analytics | Query timeouts (5s), materialized views for heavy aggregates, result caching | Load test in Phase 13 |
| Recursive outbox flooding | Events | Max fan-out depth 3; dead-letter after 5 attempts | Outbox loop test |

### E — Elevation of Privilege

| Threat | Component | Mitigation | Test |
|--------|-----------|------------|------|
| Role escalation via API | Auth | Permission to manage roles requires `identity:role:manage`; cannot grant permissions you don't have | Role escalation test |
| Tenant context injection | RLS | `app.current_tenant` set only from authenticated user's verified org; cannot be overridden from request | Context injection test |
| Admin endpoint exposure | API | Admin routes require `is_platform_admin` flag on user (platform-level, not org-level) | Unauthorized admin access → 403 |
| SSRF via inverter connector URLs | Telemetry | Connector URLs validated against allowlist; private IP ranges blocked | SSRF test |
| Path traversal in storage keys | Storage | Storage keys are computed from SHA-256 hash, never from user-provided filenames | Path traversal test |
| Mass assignment | API | Pydantic models with explicit field lists; no `**kwargs` passthrough to ORM | Mass assignment test |

---

## Mitigations Summary by Priority

| Priority | Control | Phase |
|----------|---------|-------|
| P0 | RLS cross-tenant isolation + test suite | Phase 1 |
| P0 | JWT short lifetime + rotation | Phase 1 |
| P0 | Audit append-only + hash chain | Phase 1 |
| P0 | RFC 7807 error model (no stack traces) | Phase 1 |
| P1 | Content-addressed storage + virus scan | Phase 3 |
| P1 | QR signed tokens | Phase 4 |
| P1 | Rate limiting on auth + import | Phase 1 |
| P1 | Field-level encryption for PII | Phase 2 |
| P2 | SSRF prevention in connector URLs | Phase 11 |
| P2 | PII redaction before AI calls | Phase 12 |
| P3 | CAPTCHA seam on login | V2 |

---

## Assumptions for Legal Review

- The system stores consumer connection numbers, GPS coordinates, and roof/building information. This may constitute personal data under India's DPDP Act 2023.
- Data processing consent for use of external AI/OCR providers must be obtained per tenant and per individual where required.
- The "verified by" field on rules and the "sample data" warning are UX mitigations, not legal compliance — legal review of all seeded rules is required before production use.
- Backup and PITR retention periods should be confirmed against data retention obligations.
