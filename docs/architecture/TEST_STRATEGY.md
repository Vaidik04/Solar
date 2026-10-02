# Solar Operations OS — Test Strategy

**Date:** 2026-10-01

---

## Testing Pyramid

```
         /\
        /  \
       / E2E \        Playwright — critical user journeys
      /--------\
     / Contract \     OpenAPI → TypeScript client contract tests
    /------------\
   / Integration  \   PostgreSQL (real container), RLS, migrations
  /----------------\
 /    Unit Tests    \  Domain logic, engines, normalizers, comparators
/--------------------\
/ Property-Based Tests\ Hypothesis — normalization, DSL evaluation, comparators
```

---

## Layer 1: Unit Tests (`pytest`, high coverage target)

**Target: 85%+ coverage on domain logic; 95%+ on engines.**

Directories:
- `backend/tests/unit/engines/` — workflow engine, compliance engine, reconciliation engine, DSL evaluator
- `backend/tests/unit/domain/` — domain objects, value objects, business rules
- `backend/tests/unit/services/` — service logic (mocked DB, mocked dependencies)

Key files to unit-test:
- `compliance.engine.evaluate_rule()` — exhaustive truth table for each condition type
- `reconciliation.comparators.*` — each comparator with synthetic fixtures
- `workflow.engine.can_transition()` — all guard combinations
- `platform.audit.hash_chain.compute_hash()` and `verify_chain()`
- `core.plant_id.allocate()` — gapless, no duplicates
- `assets.serial_normalizer.normalize()` — Hypothesis property tests

---

## Layer 2: Property-Based Tests (`hypothesis`)

**Target: all normalizers, all comparators, DSL condition evaluators.**

```python
# Example: Serial normalizer must be idempotent
@given(st.text())
def test_serial_normalize_idempotent(s):
    assert normalize_serial(normalize_serial(s)) == normalize_serial(s)

# Example: Compliance evaluation is deterministic
@given(project_facts_strategy(), rule_versions_strategy())
def test_compliance_deterministic(facts, rules):
    result_a = evaluate_rules(facts, rules)
    result_b = evaluate_rules(facts, rules)
    assert result_a == result_b
```

Golden files: `tests/fixtures/golden/reconciliation/` — realistic project snapshots including deliberately corrupted data (duplicate serials, capacity mismatches, missing documents). Golden tests assert exact structured output.

---

## Layer 3: Integration Tests (`pytest` + `testcontainers`)

**Target: every SQL query, every RLS policy, every migration.**

Setup: `testcontainers-python` spins up PostgreSQL 16 + TimescaleDB. Each test gets a fresh schema from running all migrations up. Teardown drops the test database.

Required integration test suites:

### 3a. RLS Cross-Tenant Penetration Suite
```
tests/integration/security/test_cross_tenant.py
```
For every CRUD endpoint, creates two orgs (Org A, Org B), populates data in Org A, authenticates as Org B, and asserts:
- List endpoints return 0 results (not Org A's data)
- Get-by-ID returns 404 (not 403 — do not reveal existence)
- Mutate endpoints return 403

This suite is the Phase 1 acceptance gate.

### 3b. Migration Tests
```
tests/integration/migrations/test_migrations.py
```
- `alembic upgrade head` on clean DB: no errors
- `alembic downgrade -1` then `upgrade +1`: no errors, no data loss (tested with seed data)
- Schema hash test: committed schema hash matches actual DB after migrations

### 3c. Audit Chain Tests
```
tests/integration/audit/test_hash_chain.py
```
- Insert 100 events, verify chain passes
- Modify one row (bypassing app), verify chain fails at correct position
- Delete one row, verify gap detection
- Checkpoint test: checkpoint HMAC verifies correctly; replayed checkpoint after rollback fails

### 3d. Idempotency Tests
```
tests/integration/idempotency/test_idempotency_keys.py
```
- Same key + same payload: returns original response, no second mutation
- Same key + different payload: returns 409
- Expired key (>24h): treated as new request
- Concurrent requests with same key: exactly one executes

### 3e. Outbox Tests
```
tests/integration/outbox/test_outbox_delivery.py
```
- Event written atomically with state change
- Transaction rollback does not write outbox event
- Dead-letter after 5 failures
- Replay of dead-letter event

---

## Layer 4: Contract Tests

**Source of truth: `openapi.json` committed to repo.**

```
tests/contract/test_openapi_schema.py
```
- Every API route has a documented request/response schema
- TypeScript client types generated from OpenAPI do not have type errors (`tsc --noEmit`)
- Example values in OpenAPI pass schema validation

---

## Layer 5: End-to-End Tests (`playwright` + test server)

**Target: critical user journeys, smoke on every build.**

Critical journey test (`tests/e2e/test_critical_journey.py`):

```
1. Create organization + admin user
2. Create customer + site
3. Create project (get SOL-MP-000001)
4. Submit design + BOM
5. Bulk import 10 assets (CSV)
6. Run reconciliation → assert MISMATCH detected (seeded mismatch in BOM)
7. Fix mismatch → re-run → MATCH
8. Run compliance → assert PASS
9. Generate WCR → assert validation gate
10. Record inspection → commissioning readiness
11. Commission project → assert stage = COMMISSIONED
12. Create warranty → create O&M plan
13. Create ticket → resolve → assert SLA clock
14. Verify audit chain → PASS
```

---

## Layer 6: Security Tests

**Authorization matrix (`tests/security/test_authz_matrix.py`):**

Generates a matrix of `(role, endpoint, method, own_resource, other_resource)` and verifies expected allow/deny against the central policy module. Matrix is data-driven from a YAML fixture — easy to extend when permissions change.

**Brute force / rate limit tests:** verify lockout after N failures, verify rate limit headers, verify 429 response.

---

## Layer 7: Sync Chaos Tests (V2 / Phase 10)

```
tests/sync/test_chaos.py
```
- Duplicate delivery: same mutation delivered twice → idempotent result
- Out-of-order delivery: events processed in wrong order → consistent final state
- Concurrent edits: serial change + photo upload from same device simultaneously
- Network partition: partial upload with resumption

---

## Layer 8: Load Tests (`locust`)

```
tests/load/locustfile.py
```

**Targets at data volume: 500 projects / 50k assets / 5M telemetry rows:**

| Endpoint | p95 target |
|----------|-----------|
| GET /v1/projects (list, 50 results) | < 200ms |
| GET /v1/projects/{id} (Plant Passport) | < 500ms |
| GET /v1/dashboard/summary | < 1s |
| POST /v1/reconciliation/runs | < 2s (async, job queued < 100ms) |
| GET /v1/generation/summary (30 days) | < 500ms (from continuous aggregate) |

---

## CI Pipeline Requirements

Every commit runs (in order, blocking):
1. `ruff check` (lint)
2. `mypy --strict` (type check)
3. `pytest tests/unit -x` (unit tests)
4. `pytest tests/unit --hypothesis-seed=0` (property tests)
5. `pytest tests/integration -x --db-url=...` (integration, real DB)
6. `pytest tests/security -x` (cross-tenant + authz matrix)
7. `pytest tests/contract` (OpenAPI contract)
8. `alembic upgrade head && alembic downgrade -1 && alembic upgrade head` (migration round-trip)
9. `import-linter --config .importlinter` (module boundary check)
10. `safety check` (dependency CVE scan)
11. `trivy image ...` (container scan, on main branch)
12. `playwright test` (E2E, against ephemeral environment)

Any failure blocks merge. No overrides without a written incident note.
