# mineproductivity.kpis

## Purpose

The KPI metadata model and the Standard KPI Library described in Developer & Cookbook Guide — Part III: definitions, units, provenance, and formula contracts for mining productivity KPIs.

## Scope

**What belongs here:**
- KPI metadata schema (units, provenance, validity windows, versioning).
- The KPI registry contract and standard KPI catalog entries (metadata only at this phase).

**What must never belong here:**
- Actual KPI calculation logic — this phase is metadata/contract only, per the project's zero-business-logic constraint.
- Analytics, optimization, or decision logic built on top of KPI values (see `analytics`, `decision`).

## Responsibilities

- Implements the `kpis` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`

**Depended on by:** `analytics`, `decision`, `digital_twin`, `benchmark`, `certification`

## Future Work

Implement `kpis` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
