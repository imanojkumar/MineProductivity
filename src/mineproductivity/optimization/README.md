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

**Depends on:** `core`, `ontology`, `kpis`, `analytics`, and, per `decision`/`digital_twin`/`simulation`'s own locked Future Roadmap sections, expected to also consume `decision.ActionPlan`, `digital_twin`'s twin-state types, and `simulation.Experiment`/`ExperimentResult` (and to become a plausible first implementer of `simulation.CalibrationModel`) once designed.

**Depended on by:** not yet consumed by another package. `decision` does **not** depend on `optimization` — Decision Intelligence spec 07 §36 explicitly states it "does not anticipate `decision` ever needing to call into a future `optimization`/`simulation` package."

## Future Work

Implement `optimization` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
