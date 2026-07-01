# mineproductivity.registry

## Purpose

The generic registry mechanism enabling plugin-first discovery of KPIs, connectors, analytics, and agents.

## Scope

**What belongs here:**
- Generic, type-parameterized registry interfaces (register/lookup/list).

**What must never belong here:**
- Concrete registrations of KPIs, connectors, or agents — those live in `plugins` or the owning package.
- Imports from `kpis`, `analytics`, `decision`, `digital_twin`, `agents`, `connectors`, `optimization`, or `simulation`.

## Responsibilities

- Implements the `registry` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `exceptions`

**Depended on by:** `plugins`, `kpis`, `connectors`, `analytics`, `agents`

## Future Work

Implement `registry` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
