# mineproductivity.digital_twin

## Purpose

State representation and synchronization for the live digital twin of mining assets and processes, built as a projection of the event stream.

## Scope

**What belongs here:**
- Twin state model interfaces and synchronization contracts.
- Projection interfaces from `events`/`kpis` into twin state.

**What must never belong here:**
- Raw connector ingestion (see `connectors`).
- Decision/recommendation logic (see `decision`).

## Responsibilities

- Implements the `digital_twin` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `kpis`, `analytics`, `simulation`

**Depended on by:** `decision`, `agents`, `visualization`

## Future Work

Implement `digital_twin` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
