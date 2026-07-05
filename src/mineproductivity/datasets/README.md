# mineproductivity.datasets

## Purpose

Dataset abstractions and loader contracts for canonical, golden, benchmark, and synthetic datasets used across the platform (distinct from the top-level `datasets/` directory, which holds the actual data files).

## Scope

**What belongs here:**
- Dataset descriptor and loader interfaces.
- Dataset metadata (schema, provenance, licensing) contracts.

**What must never belong here:**
- The actual dataset files (see top-level `datasets/`).
- Connector-specific ingestion logic (see `connectors`).

## Responsibilities

- Implements the `datasets` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`

**Depended on by:** `benchmark`, `certification` (once implemented). Not currently `kpis` — the implemented `kpis` package's tests and examples use their own `tests/fixtures/kpis` sample-dataset loader, a separate, already-existing mechanism independent of this still-unimplemented package.

## Future Work

Implement `datasets` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
