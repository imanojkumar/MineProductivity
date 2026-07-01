# mineproductivity.certification

## Purpose

In-package conformance/certification interfaces supporting the top-level `certification/` suite that validates an implementation against the Reference Implementation Blueprint.

## Scope

**What belongs here:**
- Certification check and reference-output comparison interface contracts.

**What must never belong here:**
- The certification golden datasets themselves (see top-level `certification/`).

## Responsibilities

- Implements the `certification` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `kpis`, `benchmark`, `validation`

**Depended on by:** Not yet consumed by another package.

## Future Work

Implement `certification` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
