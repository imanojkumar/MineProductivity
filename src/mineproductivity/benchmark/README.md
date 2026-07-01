# mineproductivity.benchmark

## Purpose

In-package benchmark harness interfaces supporting the top-level `benchmark/` scenarios and the Learning & Benchmark Suite v1.0.

## Scope

**What belongs here:**
- Benchmark harness and scoring interface contracts.

**What must never belong here:**
- The benchmark scenario definitions/data themselves (see top-level `benchmark/`).

## Responsibilities

- Implements the `benchmark` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `kpis`, `datasets`

**Depended on by:** `certification`

## Future Work

Implement `benchmark` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
