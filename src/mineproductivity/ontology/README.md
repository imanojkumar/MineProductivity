# mineproductivity.ontology

## Purpose

The explicit, machine-readable domain vocabulary for mining productivity: asset types, process types, relationships, and schema definitions that all other packages model against.

## Scope

**What belongs here:**
- Domain concept and schema definitions (assets, processes, roles, relationships).
- Ontology versioning and validation rules for domain vocabulary.

**What must never belong here:**
- Event schemas or event processing logic (see `events`).
- KPI definitions or formulas (see `kpis`).
- Any connector- or storage-specific representation.

## Responsibilities

- Implements the `ontology` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`

**Depended on by:** `events`, `kpis`, `analytics`, `decision`, `digital_twin`

## Future Work

Implement `ontology` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
