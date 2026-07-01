# mineproductivity.exceptions

## Purpose

The shared exception hierarchy used across all MineProductivity packages.

## Scope

**What belongs here:**
- Base and common exception class definitions.

**What must never belong here:**
- Domain-specific error handling logic — only the exception types/hierarchy live here.
- Imports from any package other than `core`.

## Responsibilities

- Implements the `exceptions` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`

**Depended on by:** `every layer`

## Future Work

Implement `exceptions` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
