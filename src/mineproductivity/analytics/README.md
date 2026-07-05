# mineproductivity.analytics

## Purpose

Statistical and analytical processing built on top of KPI and event data — trend analysis, correlation, and descriptive analytics.

## Scope

**What belongs here:**
- Analytical model interfaces and pipeline contracts.
- Descriptive/statistical analysis built strictly on `kpis` and `events` outputs.

**What must never belong here:**
- Optimization or prescriptive logic (see `optimization`, `decision`).
- Direct connector or I/O access — analytics consumes projections, not raw sources.

## Responsibilities

- Implements the `analytics` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`, `plugins`, `kpis`. (`connectors` is a permitted import under the platform-wide layering rule but is not exercised — analytics operates on already-computed `KPIResult`s, never a vendor-specific wire format.)

**Depended on by:** `decision`, `digital_twin`, `simulation`, `optimization`, `agents`, `visualization`

## Future Work

Implement `analytics` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
