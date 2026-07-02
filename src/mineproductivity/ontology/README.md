# mineproductivity.ontology

## Purpose

The explicit, machine-readable domain vocabulary for mining productivity: asset types, process types, relationships, and schema definitions that all other packages model against.

## Scope

**What belongs here:**
- Domain concept and schema definitions (assets, processes, roles, relationships).
- Ontology versioning and validation rules for domain vocabulary.

**What must never belong here:**
- Event schemas or event processing logic (see `events`).
- KPI definitions or formulas (see `kpis`).
- Any connector- or storage-specific representation.

## Responsibilities

- Implements the `ontology` subsystem as defined in the Reference Implementation Blueprint v1.0.
- The full Ontology Framework (entity types, registry, relationships, reasoning) is not yet implemented — it is scheduled for its own milestone per [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md).

## Status Exception — Documentation Governance Rule #005

One minimum shared contract has been published ahead of the full Ontology Framework milestone, because the locked Event Framework design specification requires it to type `DelayEvent.delay_category`: the six-value `DelayCategory` enum (`ontology/reference/delay_taxonomy.py`). This is the *only* symbol this package currently implements or exports.

Per Documentation Governance Rule #005: *when a package depends on a future package, only the minimum shared contract (types, enums, immutable value objects, or interfaces) may be introduced into the owning package. No business logic, services, registries, or engines from the future package may be implemented before its scheduled milestone.* No equipment types, location/organization/production/maintenance/cost/quality/safety/environmental ontologies, `BaseEntityType`, relationships, or the Knowledge Graph projection contract exist yet — only `DelayCategory`.

## Contents

- `__init__.py` — exports `DelayCategory` only.
- `reference/delay_taxonomy.py` — the `DelayCategory` enum and its precedence order.
- `README.md` — this file.

## Dependencies

**Depends on:** `core` (indirectly, via `enum.Enum`; `DelayCategory` itself has no runtime dependency beyond the standard library).

**Depended on by:** `events` (imports `DelayCategory` for `DelayEvent.delay_category`); will be depended on by `kpis`, `analytics`, `decision`, `digital_twin` once those packages are implemented.

## Future Work

Implement the remaining nine sub-ontology families, `BaseEntityType`, relationships, and the Knowledge Graph projection contract per [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md) and [`docs/design/02_Ontology_Implementation_Checklist.md`](../../../docs/design/02_Ontology_Implementation_Checklist.md), tests-first, at that package's scheduled milestone.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md)
- [`docs/architecture/01_Event_Framework_Design_Specification.md`](../../../docs/architecture/01_Event_Framework_Design_Specification.md) (the consumer requiring this contract)
