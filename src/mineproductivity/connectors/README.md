# mineproductivity.connectors

## Purpose

Interfaces and reference implementations for integrating external mining systems (fleet management, ERP, IoT/sensor feeds) as sources of events.

## Scope

**What belongs here:**
- Connector interface/protocol definitions.
- Reference/example connector scaffolding (structure only at this phase).

**What must never belong here:**
- Core domain or ontology logic.
- Direct KPI computation — connectors only produce events/data, they do not compute KPIs.

## Responsibilities

- Implements the `connectors` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `io`, `config`

**Depended on by:** `digital_twin`, `agents`

## Future Work

Implement `connectors` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
