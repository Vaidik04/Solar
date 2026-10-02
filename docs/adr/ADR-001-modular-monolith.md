# ADR-001: Modular Monolith Architecture

**Status:** Accepted  
**Date:** 2026-10-01  
**Deciders:** Lead Architect

## Context

The platform covers 15 bounded contexts. We must choose between microservices, monolith and modular monolith. The team is small, data volume is moderate, and we need rapid iteration in V1 while preserving the ability to scale out specific modules in V2/V3.

## Options Considered

1. **Microservices from day 1** — Operational complexity (18+ services, distributed transactions, service mesh) is unjustified at this scale. Cross-cutting concerns (tenancy, audit, RLS) become a distributed systems problem. Rejected.
2. **Big ball of mud monolith** — No boundaries, no future extraction path. Rejected.
3. **Modular monolith** — Strict module boundaries enforced by import linting. Single deployable in V1. Extraction of hot modules (compliance, reconciliation, telemetry) to separate services is achievable because the interface contracts are already defined via service interfaces and domain events. **Accepted.**

## Decision

Modular monolith. Every module owns its tables, models, service interface and events. Cross-module access only via `module.service` (sync) or domain events (async). Enforced by `import-linter` in CI.

## Consequences

- **Good:** Fast iteration, single transaction boundary for atomic operations, simpler observability setup.
- **Good:** Extraction seams built in from day 1.
- **Risk:** Boundary discipline requires CI enforcement — if import linter is disabled, boundaries collapse. Mitigation: lint check is required, not optional, in CI.
