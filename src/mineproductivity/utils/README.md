# mineproductivity.utils

## Purpose

Small, dependency-free cross-cutting utility functions with no domain knowledge.

## Scope

**What belongs here:**
- Generic helpers (string/date/collection utilities) with no domain semantics.

**What must never belong here:**
- Anything with domain meaning — if it knows about assets, KPIs, or events, it does not belong here.
- Imports from any package other than `core`.

## Responsibilities

- Implements the `utils` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`

**Depended on by:** `every layer`

## Future Work

Implement `utils` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
