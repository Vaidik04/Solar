# ADR-005: RBAC + ABAC Central Policy Module

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Authorization decisions must be consistent, auditable, and maintainable. Scattered `if user.role == "admin"` checks throughout the codebase are a maintenance and security nightmare.

## Decision

A **single policy module** (`core.policy`) is the only place authorization decisions are made. It evaluates:

1. **RBAC layer:** `user → memberships → roles → permissions`. A permission is a string like `project:create`, `asset:bulk_import`, `compliance:waive`. Roles are defined per-organization (custom) or from the platform default set.

2. **ABAC constraints** (evaluated after RBAC grants the permission type):
   - `branch_constraint`: user may only see projects in their branch(es)
   - `assigned_constraint`: user may only see projects they are assigned to
   - `ownership_constraint`: user may only modify resources they created
   - `plan_constraint`: feature gates by organization subscription plan

Policy check signature:
```python
async def authorize(
    user: UserContext,
    permission: str,            # e.g. "project:transition"
    resource: AuthzResource,    # subject with org_id, branch_id, owner_id
    action_context: dict = {},  # extra facts for ABAC rules
) -> AuthzResult:               # allow / deny with reason
```

Every API endpoint uses `Depends(require_permission("project:transition"))`. The dependency injects and evaluates `authorize(...)`. Failure raises `403 Forbidden` with problem-details body.

The policy module is the **only** place that reads the permission tables. No other module may query `role`, `permission`, or `membership` tables directly.

Permissions are seeded as data; adding a new permission requires a migration + seeding, no code change to the auth module.

## Alternatives Considered

- **OPA (Open Policy Agent)** — Adds sidecar infra, HTTP latency per request. For V1 volume, in-process evaluation is fast enough. Clean seam to switch later.
- **Per-module permission checks** — Not acceptable; permissions become inconsistent.

## Consequences

- **Good:** All authorization logic in one testable place.
- **Good:** Authorization matrix tests can enumerate all permissions × all roles systematically.
- **Risk:** The policy module becomes a bottleneck. Mitigation: permission evaluation is pure computation over cached user context (loaded once per request into `UserContext`); no DB queries during evaluation.
