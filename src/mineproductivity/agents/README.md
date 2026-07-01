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

**Depends on:** `core`, `ontology`, `events`, `kpis`, `analytics`, `decision`, `digital_twin`, `connectors`

**Depended on by:** `cli`, `visualization`

## Future Work

Implement `agents` per its phase in ROADMAP.md, tests-first, following the metadata-first and plugin-first principles described in the root README.md.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
