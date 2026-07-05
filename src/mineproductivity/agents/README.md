# mineproductivity.agents

## Purpose

AI agent orchestration built atop the decision layer — the outermost intelligence layer that composes lower layers into autonomous or semi-autonomous workflows.

## Scope

**What belongs here:**
- Agent orchestration interfaces and contracts.
- Agent tool/action contracts scoped to lower-layer interfaces.

**What must never belong here:**
- Any core domain, ontology, event, or KPI logic — agents consume these layers, they do not define them.

## Responsibilities

- Implements the `agents` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Currently contains no implementation — structural placeholder only.

## Contents

- `__init__.py` — package marker (no public API yet).
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, `digital_twin`, `simulation` — not `connectors` directly: per every locked spec below it (`analytics` spec 06 §5, `decision` spec 07 §5, `digital_twin` spec 08 §5, `simulation` spec 09 §5), the platform-wide convention is to operate on already-computed, already-event-sourced facts, never a vendor-specific wire format.

**Depended on by:** `cli`, `visualization`

## Future Work

Implement `agents` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
