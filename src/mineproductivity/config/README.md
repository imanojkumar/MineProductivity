# mineproductivity.config

## Purpose

Cross-cutting configuration loading, schema, and environment management used by any layer.

## Scope

**What belongs here:**
- Configuration schema and loader interfaces.

**What must never belong here:**
- Domain-specific configuration values — those belong with the consuming package's own metadata.
- Imports from `kpis`, `analytics`, `decision`, `digital_twin`, `agents`, `connectors`, `optimization`, or `simulation`.

## Responsibilities

- Implements the `config` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`

**Depended on by:** `every layer`

## Future Work

Implement `config` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
