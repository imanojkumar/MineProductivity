# mineproductivity.events

## Purpose

The event schema and event-sourcing primitives that make the immutable event stream the system of record for all derived state.

## Scope

**What belongs here:**
- Event schema definitions, event envelopes, and event-store interfaces.
- Event versioning and replay/projection contracts.

**What must never belong here:**
- Concrete connector implementations that produce events (see `connectors`).
- KPI computation logic that consumes events (see `kpis`).
- Persistence backend implementations (interfaces only; see `io` for I/O primitives).

## Responsibilities

- Implements the `events` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`

**Depended on by:** `kpis`, `analytics`, `decision`, `digital_twin`, `simulation`

## Future Work

Implement `events` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
