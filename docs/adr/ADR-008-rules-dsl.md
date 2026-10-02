# ADR-008: Declarative Rules DSL (JSON Schema-validated YAML)

**Status:** Accepted  
**Date:** 2026-10-01

## Context

Compliance rules must be authored by domain experts, versioned, audited, and evaluatable without deploying new code. Rule evaluation must be deterministic, sandboxed, and explainable.

## Decision

**JSON Schema-validated YAML DSL, evaluated by a pure Python interpreter.**

A rule document looks like:

```yaml
rule_id: R-MNRE-NET-001
version: "1.2"
title: "Net metering eligibility — residential < 10 kWp"
authority: MNRE
regulation_ref: "MNRE-NM-2023, Clause 4.2"
applicable_when:
  all:
    - field: project.scheme
      in: [net_metering, net_billing]
    - field: project.sanctioned_capacity_kwp
      lte: 10.0
    - field: site.connection_type
      eq: residential
checks:
  - id: CHK-001
    description: "Inverter capacity must not exceed sanctioned load"
    condition:
      field: design.total_inverter_capacity_kva
      lte:
        field: site.sanctioned_load_kva
    severity: fail
    message_template: "Inverter capacity {actual} kVA exceeds sanctioned load {limit} kVA"
    remediation: "Reduce inverter capacity or request load enhancement"
  - id: CHK-002
    description: "Net meter certificate must be present"
    condition:
      document_present:
        type: net_meter_certificate
        verified: true
    severity: fail
    message_template: "Net meter certificate not found or not verified"
requires_documents:
  - type: net_meter_certificate
  - type: discom_sanction_letter
output_severity: fail  # overall rule severity if any check fails
```

DSL capabilities:
- Conditions: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`, `exists`, `not_exists`, `all`, `any`, `not`
- Field references: dot-notation paths into project facts (pre-computed snapshot)
- Document checks: `document_present`, `document_verified`, `document_not_expired`
- Asset checks: `assets_count`, `assets_all_installed`, `serials_match_bom`
- Date checks: `date_before`, `date_after`, `within_days`
- No arbitrary code execution, no external calls, no side effects

The evaluator:
- Receives a `ProjectFactsSnapshot` (pure dict, immutable)
- Receives a list of `RuleVersion` objects
- Returns `ComplianceResult` list with full reasoning trace (which conditions passed/failed, what values were compared)
- Is a pure function — same inputs always produce same outputs
- Runs in the same process, no subprocess/eval/exec

## Alternatives Considered

- **Python code as rules (with restricted exec)** — Sandboxing is hard; security risk; not auditable by non-programmers. Rejected.
- **Drools / Rete engine** — JVM dependency; over-engineered. Rejected.
- **SQL-based rules** — Good for simple checks but cannot represent complex condition trees or document checks. Rejected.

## Consequences

- **Good:** Rules are data — authored in admin UI, versioned in DB, exportable.
- **Good:** Evaluation is deterministic and reproducible given the same inputs and rule versions.
- **Good:** Non-engineers can understand and author rules with tooling.
- **Risk:** DSL expressiveness is limited. Mitigation: the DSL covers the identified rule patterns; complex edge cases get a `custom_check_type` that maps to a registered Python check function (still versioned, still audited, but requires code deployment).
