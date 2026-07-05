# mineproductivity.simulation

## Purpose

Simulation engines for projecting a mining system's state forward under a hypothetical or historical scenario — orchestrating pluggable Monte Carlo, discrete-event, system-dynamics, and calibration models, seeded from real `digital_twin` snapshots and event history, without owning KPI computation, statistics, or decision logic itself.

## Scope

**What belongs here:**
- Simulation engine interfaces and scenario contracts.

**What must never belong here:**
- Live digital twin state management (see `digital_twin`).
- Optimization solving (see `optimization`).

## Responsibilities

- Implements the `simulation` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`, `plugins`, `kpis`, `analytics`, `decision`, `digital_twin`. (`connectors` is a permitted import under the platform-wide layering rule but is not exercised — simulation operates on already-computed, already-synchronized facts, never a vendor-specific wire format.)

**Depended on by:** `optimization`, `agents`, `visualization`

## Future Work

Implement `simulation` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
