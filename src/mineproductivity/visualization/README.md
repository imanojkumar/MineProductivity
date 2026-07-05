# mineproductivity.visualization

## Purpose

Dashboards and visual reporting for KPIs, analytics, decisions, digital twin state, and simulation results.

## Scope

**What belongs here:**
- Visualization interface contracts and rendering abstractions.

**What must never belong here:**
- Business/analytical logic — visualization only renders data produced by other layers.

## Responsibilities

- Implements the `visualization` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`

**Depended on by:** `cli`

## Future Work

Implement `visualization` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
