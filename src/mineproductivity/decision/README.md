# mineproductivity.decision

## Purpose

Decision-support and recommendation frameworks that translate `analytics`' statistical judgments (trends, benchmarks, confidence intervals) into recommended, ranked, explained, actionable decisions — the platform's prescriptive layer, sitting directly above `analytics`' descriptive layer.

## Scope

**What belongs here:**
- Decision/recommendation interfaces and contracts.
- Decision provenance and explainability contracts.

**What must never belong here:**
- AI agent orchestration (see `agents`).
- Presentation/visualization logic (see `visualization`).

## Responsibilities

- Implements the `decision` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`, `plugins`, `kpis`, `analytics`. (`connectors` is a permitted import under the platform-wide layering rule but is not exercised — decision operates on already-computed `KPIResult`/`AnalyticsResult` objects, never a vendor-specific wire format.)

**Depended on by:** `digital_twin`, `simulation`, `optimization`, `visualization`, `agents`, `cli`

## Future Work

Implement `decision` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
