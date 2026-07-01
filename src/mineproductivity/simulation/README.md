# mineproductivity.simulation

## Purpose

Simulation engines for modeling mining operations under hypothetical or forecast conditions, feeding the digital twin and decision layers.

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

**Depends on:** `core`, `ontology`, `events`, `kpis`

**Depended on by:** `digital_twin`, `decision`

## Future Work

Implement `simulation` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
