# mineproductivity.optimization

## Purpose

Optimization models and solver interfaces for productivity improvement recommendations (e.g., scheduling, allocation).

## Scope

**What belongs here:**
- Optimization problem/model interfaces.
- Solver adapter contracts.

**What must never belong here:**
- Simulation execution logic (see `simulation`).
- Decision presentation or recommendation delivery (see `decision`).

## Responsibilities

- Implements the `optimization` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `kpis`, `analytics`

**Depended on by:** `decision`

## Future Work

Implement `optimization` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
