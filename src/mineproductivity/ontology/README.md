# mineproductivity.ontology

## Purpose

`mineproductivity.ontology` is the typed, machine-readable model of the mining world: ten sub-ontology families (equipment, material, location, organization, production, maintenance, cost, quality, safety, environmental) built on a single entity-type root (`BaseEntityType`), connected by explicit `Relationship` edges, validated both structurally (at construction) and contextually (`OntologyValidator`), and projectable into a Knowledge Graph via `KnowledgeGraphProjection` — so no other package ever needs to invent its own notion of "what a haul truck is" or "which delay categories exist."

This package implements the [Ontology Framework Design Specification](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md) exactly. Where this README and that specification disagree, the specification governs.

## Scope

**What belongs here:**

- The entity-type root (`BaseEntityType`, `EntityTypeMetadata`) and its structural validation hook.
- Every concrete entity type across the ten sub-ontology families, each a leaf of `BaseEntityType` (or, for equipment, of the `EquipmentType` intermediate).
- `Relationship`/`RelationshipKind` — explicit, typed edges between entity ids.
- `OntologyValidator` — contextual, cross-entity referential validation.
- `KnowledgeGraphProjection`, `GraphNode`, `GraphEdge` — the contract a future Knowledge Graph builder consumes.
- Closed, governed reference taxonomies consumed by other packages (`DelayCategory`, `SafetyEventType`).

**What must never belong here:**

- Event schemas or event processing logic (see `events`).
- KPI definitions or formulas (see `kpis`).
- Any connector- or storage-specific representation (see `connectors`).
- A generic, cross-package registry/plugin-discovery mechanism (see `registry`) — this package's internal entity-type registry is a minimal, self-contained stand-in, not that mechanism (see Future Work below).
- Instance-level persistence. `ontology` defines *types* and the *shape* of relationships; it never stores or looks up actual entity instances (that is a future `config`/datasets-loader concern, consumed through `OntologyValidator`'s optional `entity_resolver` callback).
- Graph traversal (`neighbors`/`path`/`search`). `KnowledgeGraphProjection` only *emits* nodes/edges; traversal belongs to a future graph-adjacent capability that *consumes* this projection (design spec §4).

## Architecture

`ontology` sits directly above `core` in the dependency chain and depends on nothing else:

```
core  →  ontology  →  events  →  kpis  →  ...
```

Every concrete entity type is a frozen, slotted dataclass subclassing `BaseEntityType`, declaring:

- `code: ClassVar[str]` — the stable registry key (e.g. `"RIGID_HAUL_TRUCK"`).
- `meta: ClassVar[EntityTypeMetadata]` — descriptive metadata, including `supported_kpis` (the metadata-first principle: a KPI namespace this type participates in is declared on the type, not inferred).
- Whatever domain fields the type needs.

Two validation layers apply, each with a distinct purpose:

1. **Structural validation, at construction** (`BaseEntityType.__post_init__` → `_normalize()` → `validate()`). Enforces invariants a single instance can check on its own (`Bench.pit_id must not be empty`, `Shift.end_utc must be after start_utc`). Raises `OntologyValidationError` immediately — invalid state can never exist.
2. **Contextual validation, on demand** (`OntologyValidator.validate()`). Enforces cross-entity referential integrity a single instance cannot check alone: does `Fleet.equipment_type_code` name a real, registered entity type? Does `Bench.pit_id` name a `Pit` that actually exists in this dataset? The first check is self-contained (this package owns its own type registry); the second requires an injected `entity_resolver` callback, since `ontology` does not persist instances. An unresolved reference is always a *warning* in the returned `ValidationResult`, never a raised exception.

`core.BaseEntity` (the identity-based-equality base every entity in the platform ultimately derives from) does not define a `__post_init__`/`validate()` hook of its own — no package built entity *types* on top of it before this one. `BaseEntityType` adds that hook locally, mirroring `core.BaseValueObject`'s existing `_normalize()`/`validate()` pattern exactly, without modifying the locked `core` package.

See the [design specification's §10](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md) for the full object model and class diagrams.

### Documentation Governance Rule #005

`events.DelayEvent.delay_category` and `events.SafetyEvent.safety_event_type` are typed against enums this package owns: `DelayCategory` and `SafetyEventType`. Both are closed, governed taxonomies — domain reference *data*, not event *structure* — so they are owned here, not by `events`, per design spec AD-ON-03. `events` imports both directly rather than defining its own copy; this is mechanically checked by `tests/unit/events/test_public_api.py::TestNoForbiddenDependencies::test_only_ontology_dependency_is_delaycategory_and_safetyeventtype`.

`DelayCategory` was published ahead of this package's own milestone (during the Event Framework's implementation, v0.3.0) as the minimum shared contract Documentation Governance Rule #005 permits; it now lives at its permanent home, `ontology/reference/delay_taxonomy.py`, unchanged.

## Package Structure

```
ontology/
├── __init__.py                    # public API surface (__all__)
├── entity_type.py                 # BaseEntityType, EntityTypeMetadata, the entity type registry
├── relationship.py                # Relationship, RelationshipKind
├── graph_projection.py            # KnowledgeGraphProjection, GraphNode, GraphEdge
├── validation.py                  # OntologyValidator
├── exceptions.py                  # the ontology exception hierarchy
├── equipment/                     # EquipmentType root + 12 leaf types
│   ├── equipment_type.py            # EquipmentType, OperationalState
│   ├── haul_truck.py                  # RigidHaulTruck, ArticulatedHaulTruck
│   ├── loading_unit.py                  # HydraulicShovel, WheelLoader, LHD
│   ├── drill.py                           # BlastholeDrill
│   ├── ancillary.py                         # Dozer, Grader, WaterTruck
│   └── fixed_plant.py                         # Crusher, Conveyor, Mill
├── material/                      # Commodity, MaterialType
├── location/                      # Mine, Pit, Bench, Zone, Route, Level, Stope, Drive
├── organization/                  # Fleet, Crew, Operator, BusinessUnit, Contractor
├── production/                    # Shift, ShiftPattern, ShiftCalendar
├── maintenance/                   # FailureMode, MaintenanceWorkOrder
├── cost/                          # CostCenter, CostCategory
├── quality/                       # GradeAttribute, QualitySpecification
├── safety/                        # HazardZone, SpeedLimitMap, SafetyEventType
├── environmental/                 # EmissionFactor, MonitoringPoint
├── reference/                     # DelayCategory (published ahead of schedule for events, v0.3.0)
└── README.md                      # this file
```

## Dependency Rules

```
core  →  ontology
```

- **`ontology` depends on:** `core` only. No other package.
- **`ontology` is depended on by:** `events` (reference taxonomies only), `connectors` and `kpis` (the entity-type vocabulary directly), and transitively `analytics`, `decision`, `digital_twin`, and `simulation`. `registry` does **not** depend on `ontology` — `registry` is a lower-level, domain-agnostic mechanism that only `core` sits below.
- **Forbidden:** `ontology` must never import `events`, `registry`, `connectors`, `kpis`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`. This is mechanically checked by `tests/unit/ontology/test_public_api.py::TestNoForbiddenDependencies`.

## Public API

```python
from mineproductivity.ontology import (
    # Root
    BaseEntityType, EntityTypeMetadata, Relationship, RelationshipKind,
    # Equipment
    EquipmentType, OperationalState,
    RigidHaulTruck, ArticulatedHaulTruck,
    HydraulicShovel, WheelLoader, LHD,
    BlastholeDrill, Dozer, Grader, WaterTruck,
    Crusher, Conveyor, Mill,
    register_equipment,
    # Material
    Commodity, MaterialType,
    # Location
    Mine, Pit, Bench, Route, Zone, Level, Stope, Drive,
    # Organization
    Fleet, Crew, Operator, BusinessUnit, Contractor,
    # Production
    Shift, ShiftPattern, ShiftCalendar,
    # Maintenance
    FailureMode, MaintenanceWorkOrder,
    # Cost
    CostCenter, CostCategory,
    # Quality
    GradeAttribute, QualitySpecification,
    # Safety
    HazardZone, SpeedLimitMap, SafetyEventType,
    # Environmental
    EmissionFactor, MonitoringPoint,
    # Reference
    DelayCategory,
    # Graph
    KnowledgeGraphProjection, GraphNode, GraphEdge,
    # Validation
    OntologyValidator,
    # Exceptions
    OntologyValidationError, UnknownEntityTypeError, RelationshipError,
)
```

The entity type registry's lookup functions (`lookup_entity_type`, `get_entity_type`, `registered_entity_type_codes`) are internal (design spec §9 — the Registry Framework, `registry`, owns the public discovery surface) and are imported from `mineproductivity.ontology.entity_type` directly, not the top-level namespace.

## Extension Guide

**Adding a new equipment leaf type.** Subclass `EquipmentType`, declare a unique `code`, a fully-populated `meta: EntityTypeMetadata` (including `supported_kpis`), and any type-specific fields as `kw_only` dataclass fields with defaults. Apply `@register_equipment` (an alias of `register_entity_type`, for readability at equipment call sites):

```python
from dataclasses import dataclass, field
from typing import ClassVar
from mineproductivity.ontology import EntityTypeMetadata, EquipmentType, register_equipment

@register_equipment
@dataclass(frozen=True, slots=True, eq=False)
class UndergroundJumbo(EquipmentType):
    code: ClassVar[str] = "UNDERGROUND_JUMBO"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Underground Jumbo Drill",
        description="A multi-boom underground drill rig for face development.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "DRILL.PenetrationRate"),
    )

    model: str = field(default="", kw_only=True)
    boom_count: int = field(default=2, kw_only=True)
```

No existing leaf type is ever edited to add a new one. The same pattern applies to every other sub-ontology family via `register_entity_type` directly.

**Adding a new sub-ontology family.** Create a new subpackage under `ontology/`, following the existing families' shape (one or more `BaseEntityType` leaves per module, an `__init__.py` re-exporting them), then add the new symbols to `ontology/__init__.py`'s imports and `__all__` (kept alphabetically sorted — mechanically checked by `tests/unit/ontology/test_public_api.py::TestPublicApiSurface::test_all_is_sorted`).

**Declaring a relationship between two entities.** Construct a `Relationship`, never an object-graph pointer (design spec AD-ON-02) — entities remain independent, independently serializable:

```python
edge = Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id)
```

**Validating a dataset's cross-entity references.** Construct an `OntologyValidator`, optionally with an `entity_resolver` callback backed by whatever instance store the caller has (a future `config`/datasets loader, an in-memory dict during ingestion, ...):

```python
validator = OntologyValidator(entity_resolver=lambda entity_id: entity_id in known_ids)
result = validator.validate(candidate)
if not result.is_valid:
    log.warning("unresolved references: %s", result.errors)  # never raise
```

## Examples

Runnable, narrated scripts live in [`examples/ontology/`](../../../examples/ontology/README.md):

| Script | Demonstrates |
|---|---|
| `01_equipment_modelling.py` | Construct `RigidHaulTruck`/`HydraulicShovel`, inspect the shared `OperationalState` machine and declared `supported_kpis`, export a leaf type's shape as JSON Schema. |
| `02_structural_modelling.py` | Build a `Mine` → `Pit` → `Bench` structure and a `Shift`, connect entities with explicit `Relationship` edges, project the model through a `KnowledgeGraphProjection`. |
| `03_validation.py` | `OntologyValidator`'s two reference-checking modes and its "warning, never an exception" rule. |

## Design Rationale

- **Why does `BaseEntityType` add its own `__post_init__`/`validate()` hook instead of `core.BaseEntity` providing one?** `core` is locked (Documentation Governance Rule: no modifications to already-shipped packages except through their own versioned milestone). Since no package before this one built entity *types* on top of `BaseEntity`, that hook simply did not exist yet. Adding it locally, mirroring `BaseValueObject`'s already-established `_normalize()`/`validate()` pattern exactly, satisfies the design spec's "structural validation enforced at construction" requirement (§19) without touching `core`.
- **Why do `Relationship` and `KnowledgeGraphProjection` use plain string ids instead of holding direct references to the related entity objects?** Entities must remain independent and independently serializable (design spec AD-ON-02) — nesting object references would make partial datasets, lazy loading, and cross-package serialization far harder, and would silently reintroduce the very object-graph coupling `Relationship` exists to avoid.
- **Why is the entity type registry (`_EntityTypeRegistry`) internal (leading underscore, not in `__all__`) rather than a public, general-purpose registry?** The Registry Framework (`registry`, v0.5.0) owns the platform's generic, plugin-discoverable registry contract. This package's registry is a minimal, self-contained mechanism — populated at import time by `register_entity_type`, originally built so `OntologyValidator` and `to_schema()` would work without a forward dependency on `registry` before that package was implemented (Documentation Governance Rule #005, applied in reverse: `ontology` shipped before `registry`, so it carried its own small mechanism at the time). `registry` is implemented now; migrating `_EntityTypeRegistry` to delegate to `registry.Registry` without a public API change remains open (see Future Work).
- **Why is an unresolved `OntologyValidator` reference a warning, never a raised exception?** Cookbook Part I, Ch. 8's rule: one orphaned reference in a 10,000-row ingestion batch must never halt processing of the other 9,999 rows. Structural validation (which *does* raise, at construction) already guarantees no instance is internally malformed; contextual validation is strictly about cross-entity completeness, which is expected to have gaps during incremental ingestion.
- **Why do `SafetyEventType` and `DelayCategory` live in `ontology` instead of `events`, even though only `events` currently constructs values of these types?** Both are closed, governed taxonomies — domain reference *data* that outlives any one event type and that a future `kpis`/`analytics` package will also need to reference directly, not structural fields specific to how an event is shaped (design spec AD-ON-03). Defining them in `events` would have made `events` the de facto owner of domain vocabulary it does not otherwise control.
- **Why do equipment leaf types differ in which optional fields they declare (e.g. `RigidHaulTruck` has `fuel_type`, `Crusher` does not)?** Each leaf declares only the fields meaningful to that physical asset class; a haul truck's fuel type is operationally relevant (feeds `COST.FuelPerTonne`), a fixed crusher's is not modeled as a leaf-level field in this milestone. `EquipmentType.rated_capacity` and `operational_states` are the only fields every leaf is guaranteed to share.

## Anti-Patterns

- ❌ **Nesting entity objects instead of declaring a `Relationship`.** `bench.pit = pit_object` reintroduces object-graph coupling; use `Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id)`.
- ❌ **Catching the `OntologyValidator`'s output and raising on the first unresolved reference.** That defeats the entire point of returning a `ValidationResult` instead of raising — accumulate and report all errors, keep processing.
- ❌ **Reaching into `mineproductivity.ontology.entity_type._REGISTRY` directly.** Use the public functions (`lookup_entity_type`, `get_entity_type`, `registered_entity_type_codes`); the leading underscore means the internal representation may change without notice.
- ❌ **Defining a new `DelayCategory`- or `SafetyEventType`-like closed enum inside `events` "just for one new event type."** Any new closed, governed taxonomy belongs in `ontology`, not the package that happens to consume it first.
- ❌ **Skipping `@register_entity_type`/`@register_equipment` on a new leaf type "since I'm not using the registry yet."** `OntologyValidator`'s `*_type_code` resolution and `to_schema()`'s cache both depend on registration having happened at import time; an unregistered type is invisible to both.
- ❌ **Catching `Exception` instead of `OntologyValidationError`/`MineProductivityError`** when handling a rejected entity. Every exception this package raises derives from `core.MineProductivityError` specifically so callers do not need a broad `except Exception`.

## Testing & Quality

- `tests/unit/ontology/` — one `test_*.py` per source module (mirroring all ten sub-ontology family subpackages, plus `equipment/`) — **100% line coverage**, **207 tests**.
- `tests/integration/test_ontology_model.py` — a full multi-family mine model (location, equipment, organization, production, cost, safety), validated end-to-end with `OntologyValidator`, projected through a `KnowledgeGraphProjection`, and cross-checked against `events.DelayEvent`/`events.SafetyEvent` to confirm reference-data identity (not duplication).
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/ontology/`, `tests/unit/ontology/`, `tests/integration/test_ontology_model.py`, and `examples/ontology/`.
- `test_public_api.py::TestNoCircularImports` imports every submodule in isolation and confirms `importlib.reload()` is idempotent.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core` only.

**Depended on by:** `events` (`DelayCategory`, `SafetyEventType` only); `connectors` and `kpis` directly; transitively `analytics`, `decision`, `digital_twin`, and `simulation`. Not `registry` — see Dependency Rules above.

## Future Work

- The Registry Framework (`registry`, v0.5.0) is now implemented, but `_EntityTypeRegistry` has not yet been migrated to delegate to `registry.Registry` — this remains an open, tracked simplification, not a design gap; the migration is expected to be a non-breaking internal change with no public API impact.
- Once a `config`/datasets loader package exists, wire a real `entity_resolver` implementation for `OntologyValidator` instead of requiring callers to supply their own callback.
- Additional entity types (`Explosive`, `BlastPattern`, `Survey`) as further mining sub-domains are specified.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/02_Ontology_Framework_Design_Specification.md`](../../../docs/architecture/02_Ontology_Framework_Design_Specification.md)
- [`docs/design/02_Ontology_Implementation_Checklist.md`](../../../docs/design/02_Ontology_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 8 (equipment inheritance, the Knowledge Graph "never drifts from the ontology" insight)
- Developer & Cookbook Guide Part III, "Canonical Semantics" (the six-category delay taxonomy)
