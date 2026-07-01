# mineproductivity.core

## Purpose

Foundational domain primitives shared across the entire platform: base entities, value objects, identifiers, and common domain abstractions that every other package may depend on.

## Scope

**What belongs here:**
- Base entity/value-object abstractions and identity types.
- Domain-agnostic primitives (e.g., time ranges, units-of-measure scaffolding) used across subsystems.
- Abstract base classes and protocols that define shared contracts.

**What must never belong here:**
- Any KPI, event, ontology, or connector-specific logic.
- I/O, network, or persistence code (see `io`).
- Anything that imports from any other `mineproductivity` sub-package.

## Responsibilities

- Implements the `core` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** None (leaf package).

**Depended on by:** `every other package`

## Future Work

Implement `core` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
