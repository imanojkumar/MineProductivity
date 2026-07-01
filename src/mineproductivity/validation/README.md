# mineproductivity.validation

## Purpose

Cross-cutting schema and data-quality validation framework used by ontology, events, KPIs, and datasets.

## Scope

**What belongs here:**
- Validation rule interfaces and schema-validation contracts.

**What must never belong here:**
- Domain-specific validation rules — those are defined by the owning package (e.g., a KPI's own validity rules) using this framework.
- Imports from `analytics`, `decision`, `digital_twin`, `agents`, `connectors`, `optimization`, or `simulation`.

## Responsibilities

- Implements the `validation` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `exceptions`

**Depended on by:** `ontology`, `events`, `kpis`, `datasets`, `certification`

## Future Work

Implement `validation` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
