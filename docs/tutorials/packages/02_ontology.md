# Package Tutorial 2 - Ontology (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 2 of 13"
    Deep, full-surface tutorial for `mineproductivity.ontology` - the typed,
    machine-readable model of the mining world. Authored to **Package Tutorial
    Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.ontology`: the ten sub-ontology
families and the cross-cutting spine that unifies them (`BaseEntityType`, the
import-time type registry, `Relationship`/`RelationshipKind`, the
`KnowledgeGraphProjection` contract, `OntologyValidator`), the equipment
inheritance split, `to_schema()` export, and - the payoff - **adding a new
equipment leaf type with `@register_equipment`** without editing the package.

All 56 public symbols (`mineproductivity.ontology.__all__`) are accounted for
under the **coverage convention** (§5): the spine and representative leaves get
**deep** coverage (walkthrough + executed example); the remaining leaf types and
family entities - structurally identical to the ones shown - get **reference**
coverage. Public APIs only.

## Prerequisites

- [Package Tutorial 1 - Core (deep)](01_core.md): `BaseEntity`, `BaseValueObject`,
  `BaseMetadata`, `BaseValidator`/`ValidationResult`, `Maybe`, the exception
  hierarchy - **ontology is built directly on all of them** (§3).
- [Fundamentals L05 - Ontology](../fundamentals/05_ontology.md): the intro - why a
  shared vocabulary exists, typed leaves, edges-not-nesting, `Shift.contains`.

This tutorial **builds on** L05; it does not repeat the "why a vocabulary at all"
argument. If that is not yet clear, read L05 first.

## Running the examples

Every code block below is executed and its output pasted verbatim. The three
scripts live in the repository (no extras required):

```bash
pip install -e .
python examples/ontology/01_equipment_modelling.py   # ...and 02, 03
```

---

## 1. Why this package exists

`core` gives the platform domain-*free* primitives - an entity, a value object, a
repository. Something has to say what a mine actually *contains*: that a haul
truck is a type with a rated capacity and a four-state operational machine, that a
bench belongs to a pit, that a shift is a governed UTC interval, that "copper" and
"ore" and "diesel" are closed, named taxonomies. That is `ontology`.

Its job is **agreement**. "Tonnes per hour" is not a number; it is a contract
about what a truck is, when it counts as available, and what a tonne of ore means.
`ontology` writes that contract down in a form a machine can read, so a KPI
computed at one pit means the same thing at another. Every package above models
the mine using *these* types.

Two constraints define it:

- **Depends only on `core`.** Nothing mining-specific leaks downward; nothing
  above `core` is imported. This keeps the vocabulary a leaf dependency everyone
  can share.
- **Models types and structure, not live state or instances.** `ontology`
  describes what a `RigidHaulTruck` *is* and how a `Bench` relates to a `Pit`; it
  does **not** persist truck instances or track which state a truck is in *right
  now* - that is a `digital_twin` concern, derived from events (design spec
  AD-ON-04).

## 2. Architectural role

`ontology` sits one layer above `core` and below everything else:

```
core ─► ontology ─► events ─► kpis ─► analytics ─► … ─► visualization
```

Every layer above models its world with these types: an `events.ProductionEvent`
is *about* a `RigidHaulTruck` at a `Bench`; a `kpis` metric declares itself
against an equipment type's `supported_kpis`; a `digital_twin` projects the live
state of a modelled entity. Because the vocabulary is shared and governed, those
packages compose instead of each inventing "haul truck" afresh.

## 3. Integration with adjacent layers

**Downward - ontology is built directly on `core` (Tutorial 1).** This is the
clearest "consume, don't reinvent" example in the platform:

| Ontology construct | Core primitive it extends / uses |
|---|---|
| `BaseEntityType` | subclasses `core.BaseEntity[str]` - inherits identity-based equality (`eq=False` and all) |
| `EntityTypeMetadata` | subclasses `core.BaseMetadata` - adds `supported_kpis`, `parent_code` |
| `Relationship`, `GraphNode`, `GraphEdge` | subclass `core.BaseValueObject` - immutable, structural equality, `validate()` on construction |
| `OntologyValidator` | subclasses `core.BaseValidator[BaseEntityType]`; returns a `core.ValidationResult` (`success()`/`failure(*errors)`) |
| the type registry | `lookup()` returns a `core.Maybe[type]`; duplicate registration raises `core.DuplicateError` |
| `OntologyValidationError`, `UnknownEntityTypeError`, `RelationshipError` | subclass `core.ValidationError` / `NotFoundError` / `MineProductivityError` |

One subtlety worth internalizing: `core.BaseEntity` (unlike `BaseValueObject`) has
**no** `__post_init__`/`validate()` hook. Because the design spec requires
structural validation "enforced at construction" (§19), `BaseEntityType` **adds
that hook itself**, mirroring `BaseValueObject`'s `_normalize()`→`validate()`
pattern exactly - *without modifying the locked `core` package*. That is how you
extend a frozen lower layer correctly: add locally, don't reach down and edit.

**Upward:** `events`, `kpis`, `digital_twin`, and the rest consume these types.
Notably, closed governed taxonomies like `DelayCategory` and `SafetyEventType`
live *here*, not in `events` - even though `events` is their first consumer -
because they are domain reference data many packages will reference, not fields of
one event shape (design spec AD-ON-03).

## 4. Package structure

Ten sub-ontology families plus a cross-cutting spine, each a subpackage of small
modules; every public symbol is importable directly from `mineproductivity.ontology`:

| Group | Subpackage(s) | Public symbols |
|---|---|---|
| Entity-type spine | `entity_type` | `BaseEntityType`, `EntityTypeMetadata`, `register_equipment` |
| Equipment | `equipment/` | `EquipmentType`, `OperationalState`, 12 leaf types |
| Location | `location/` | `Mine`, `Pit`, `Bench`, `Level`, `Drive`, `Stope`, `Route`, `Zone` |
| Organization | `organization/` | `BusinessUnit`, `Contractor`, `Crew`, `Fleet`, `Operator` |
| Production time | `production/` | `Shift`, `ShiftCalendar`, `ShiftPattern` |
| Material | `material/` | `Commodity`, `MaterialType` |
| Quality | `quality/` | `GradeAttribute`, `QualitySpecification` |
| Cost | `cost/` | `CostCategory`, `CostCenter` |
| Environmental | `environmental/` | `EmissionFactor`, `MonitoringPoint` |
| Maintenance | `maintenance/` | `FailureMode`, `MaintenanceWorkOrder` |
| Safety | `safety/` | `HazardZone`, `SafetyEventType`, `SpeedLimitMap` |
| Reference data | `reference/` | `DelayCategory` |
| Relationships | `relationship` | `Relationship`, `RelationshipKind` |
| Knowledge graph | `graph_projection` | `KnowledgeGraphProjection`, `GraphNode`, `GraphEdge` |
| Validation | `validation` | `OntologyValidator` |
| Exceptions | `exceptions` | `OntologyValidationError`, `RelationshipError`, `UnknownEntityTypeError` |

## 5. Public APIs

All 56 exports under the **coverage convention**:

- **[deep]** - taught in a §8 walkthrough with executed output, or in the §13
  extension example.
- **[ref]** - reference coverage: documented in the **"Reference coverage"** table
  below (grouped by family; every symbol named), plus the
  [API reference](../../api-reference/ontology.md). Reserved here for the leaf
  types and family entities that are **structurally identical** to a deeply-shown
  sibling (e.g. the 10 further equipment leaves all follow `RigidHaulTruck`'s exact
  pattern) - teaching each individually would be pure repetition.

**Spine & mechanisms - [deep]**
: `BaseEntityType`, `EntityTypeMetadata`, `register_equipment`, `EquipmentType`,
  `OperationalState`, `Relationship`, `RelationshipKind`,
  `KnowledgeGraphProjection`, `GraphNode`, `GraphEdge`, `OntologyValidator`,
  `OntologyValidationError`

**Representative entities - [deep]**
: `RigidHaulTruck`, `HydraulicShovel`, `Fleet`, `Mine`, `Pit`, `Bench`, `Shift`

**Everything else - [ref]** - see the table below.

### Reference coverage

Every remaining symbol, grouped by family. Each follows the same
`BaseEntityType`/value-object pattern as its deeply-shown siblings; the one-liner
is its domain meaning.

| Family | Symbols (`[ref]`) | What they model |
|---|---|---|
| Equipment leaves | `ArticulatedHaulTruck`, `BlastholeDrill`, `Conveyor`, `Crusher`, `Mill`, `Dozer`, `Grader`, `WaterTruck`, `LHD`, `WheelLoader` | The rest of the machine fleet (frame-steered trucks, drills, fixed plant, ancillary, loaders) - each an `EquipmentType` leaf differing only in `code`/`meta`/fields. |
| Location | `Level`, `Drive`, `Stope`, `Route`, `Zone` | Underground and spatial structure: a level, a horizontal drive, an extracted stope, a haul route (source→destination + distance), a named zone. |
| Organization | `BusinessUnit`, `Contractor`, `Crew`, `Operator` | The org rollup: an enterprise business unit, a third-party contractor, a rostered crew, an equipment operator. |
| Production time | `ShiftCalendar`, `ShiftPattern` | The master shift reference table for a mine, and the common patterns (e.g. `2x12`) mines operate. |
| Material | `Commodity`, `MaterialType` | A mineral commodity (copper, iron ore, gold); whether a tonne is ore, waste, or product. |
| Quality | `GradeAttribute`, `QualitySpecification` | A measurable grade attribute (e.g. `% Cu`) and a governed acceptable range for one. |
| Cost | `CostCategory`, `CostCenter` | The cost categories a cost center classifies spend into, and a cost center scoped to a business unit. |
| Environmental | `EmissionFactor`, `MonitoringPoint` | A governed emission factor per resource type; an environmental monitoring point (dust/noise/water). |
| Maintenance | `FailureMode`, `MaintenanceWorkOrder` | A classified equipment failure mode; a work order's structural shape. |
| Safety | `HazardZone`, `SafetyEventType`, `SpeedLimitMap` | A geofenced speed-limited zone; the leading safety-indicator kinds; a mine-wide zone→speed-limit map. |
| Reference data | `DelayCategory` | The six MECE delay categories - a closed governed taxonomy `events`/`kpis` reference. |
| Exceptions | `RelationshipError`, `UnknownEntityTypeError` | Raised by a malformed `Relationship` / an unregistered type-code lookup (both derive from `core.MineProductivityError`). |

## 6. Conceptual model

Five ideas explain the package.

**A. Every type is a `BaseEntityType`.** A concrete leaf (`Pit`, `Shift`,
`RigidHaulTruck`) is a frozen dataclass declaring a unique `code: ClassVar[str]`
(the stable registry key) and a `meta: ClassVar[EntityTypeMetadata]`, plus its
domain fields. Identity-based equality comes from `core.BaseEntity`; structural
validation runs at construction.

**B. Types register themselves at import.** Applying `@register_equipment` (or the
generic `register_entity_type`) records a leaf in an import-time registry keyed by
`code`. Registration is what makes a type visible to `OntologyValidator` and
`to_schema()`. (The registry is intentionally internal for now; the `registry`
package owns the public discovery surface - design spec §9.)

**C. Structure is declared with edges, never nested pointers.** A `Bench` does not
hold a reference to its `Pit`; a `Relationship(source_id, kind, target_id)` names
the link (design spec AD-ON-02). So every entity stays independently
serializable, and the graph is a first-class thing to project and validate.

**D. Two kinds of validation, cleanly split.** *Structural* validation runs at
construction and **raises** (`OntologyValidationError`) - an instance can never
exist malformed. *Contextual* validation (`OntologyValidator`) checks cross-entity
references and **warns, never raises** - one orphaned reference must not halt
ingestion of the other 9,999 rows.

**E. The model is machine-readable.** `to_schema()` exports any type's shape as
JSON Schema, and `KnowledgeGraphProjection` exposes the entities+edges as
nodes+edges - so dashboards, integrations, and agents read the model instead of
guessing.

## 7. Real mining examples

The package *is* the mining domain, so the walkthroughs use its own types
directly (no separate mapping needed, per the template's abbreviation rule for
domain packages). The running model: a copper mine `bingham-west` → `pit-west` →
`bench-7`, a `RigidHaulTruck` and `HydraulicShovel` in `FL-NORTH`, an A-shift, and
a new `ElectricRopeShovel` added in §13.

## 8. Step-by-step walkthroughs

### 8.1 Equipment: the inheritance split, metadata, and JSON Schema

Common behaviour lives on `EquipmentType`; specifics live on the leaf. Every leaf
shares one four-state `OperationalState` machine (`OPERATING`/`STANDBY`/`DOWN`/
`MAINTENANCE`) and a `rated_capacity`; a `RigidHaulTruck` adds `fuel_type`, a
`HydraulicShovel` does not. `meta.supported_kpis` declares which metrics a type
can even support - asking a shovel for `HAUL.TKPH` is a category error the
metadata makes checkable. `to_schema()` exports the leaf's shape. Running
[`01_equipment_modelling.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/01_equipment_modelling.py):

```text
--- Construct a RigidHaulTruck ---
id=HT-214 model=CAT 797F rated_capacity=363.0t

--- Construct a HydraulicShovel loading that same fleet's trucks ---
id=SH-1 model=EX8000 rated_capacity=42.0t

--- Every leaf type shares the same four-state operational state machine ---
RigidHaulTruck.operational_states: ['operating', 'standby', 'down', 'maintenance']

--- Declared metadata drives which KPIs a leaf type supports ---
RigidHaulTruck.meta.supported_kpis: ('PROD.TruckCycleTime', 'PROD.Payload', 'UTIL.PA', 'UTIL.UA', 'HAUL.TKPH', 'HAUL.MatchFactor')
HydraulicShovel.meta.supported_kpis: ('UTIL.PA', 'UTIL.UA', 'LOAD.Rate', 'HAUL.MatchFactor')

--- A Fleet groups equipment of one type, by equipment_type_code ---
fleet FL-NORTH groups equipment_type_code='RIGID_HAUL_TRUCK'

--- Export a leaf type's shape as JSON Schema (dashboards/AI agents read this) ---
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RIGID_HAUL_TRUCK",
  "type": "object",
  "properties": {
    "rated_capacity": {
      "type": "number"
    },
    "model": {
      "type": "string"
    },
    "fuel_type": {
      "type": "string"
    },
    "fleet_id": {
      "type": "string"
    }
  },
  "required": [
    "rated_capacity"
  ]
}
```

Note the schema: only `rated_capacity` (declared on the base with no default) is
`required`; the leaf's optional fields are not. The schema is computed from the
dataclass fields and cached per type - dashboards and agents read it instead of
hard-coding a form that would drift.

### 8.2 Structure: locations, production time, and edges

`Mine` → `Pit` → `Bench` is a modelled hierarchy, not a naming convention. Note
the verified constructor shapes (these bit M1: it is `commodity_codes` **plural**,
and `RelationshipKind.BELONGS_TO`, not `PART_OF`):

```python
mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
pit = Pit(id="pit-west", mine_id=mine.id, commodity="copper")
bench = Bench(id="bench-7", pit_id=pit.id, elevation_m=1820.0)
```

The hierarchy is declared with explicit `Relationship` edges, and a `Shift` is a
governed half-open UTC interval that answers `.contains(t)`. A
`KnowledgeGraphProjection` turns the live entities+edges into nodes+edges without
ever holding a pointer between entities. Running
[`02_structural_modelling.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/02_structural_modelling.py):

```text
--- Build the structural hierarchy: Mine -> Pit -> Bench ---
bingham-west -> pit-west -> bench-7 (elevation 1820.0m)

--- Declare the edges explicitly, rather than nesting objects ---
pit-west --belongs_to--> bingham-west
bench-7 --belongs_to--> pit-west

--- Production time: a Shift is a UTC half-open interval ---
shift A-2026-06-25 contains 2026-06-25T14:30:00+00:00: True

--- Project the structural graph, computed from the live entities ---
node: bingham-west (MINE)
node: pit-west (PIT)
node: bench-7 (BENCH)
edge: pit-west -> bingham-west
edge: bench-7 -> pit-west
```

**All five `RelationshipKind`s.** L05 used only `BELONGS_TO`. The full set:
`BELONGS_TO` (Bench→Pit), `PART_OF` (Truck→Fleet), `OPERATED_BY`
(Equipment→Operator), `LOCATED_AT` (Equipment→Zone), `SCOPED_TO`
(CostCenter→BusinessUnit). Each is a *typed* edge - the kind is data, so "slice by
fleet" and "slice by pit" are different queries over the same edge set.

### 8.3 Validation: structural (raises) vs contextual (warns)

Structural validation is unconditional and raises at construction. Contextual
validation is `OntologyValidator`, which checks cross-entity references by
field-name convention and **returns a `ValidationResult` - it never raises**:

- a `*_type_code` field (e.g. `Fleet.equipment_type_code`) resolves against
  ontology's **own** registry (no help needed);
- a `*_id` field (e.g. `Bench.pit_id`) resolves against an **injected**
  `entity_resolver` callback, because ontology does not persist instances - without
  a resolver, instance references simply aren't checked.

Running [`03_validation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/03_validation.py):

```text
--- Structural validation happens at construction, always ---
constructed pit-west (would have raised OntologyValidationError if mine_id were blank)

--- OntologyValidator: *_type_code fields resolve against ontology's own registry ---
good_fleet: is_valid=True
broken_fleet: is_valid=False
  errors: ("Fleet.equipment_type_code references unknown entity type code 'NOT_A_REAL_TYPE'",)

--- *_id fields need an injected resolver, since ontology doesn't persist instances ---
good_bench: is_valid=True
orphaned_bench: is_valid=False
  errors: ("Bench.pit_id references unresolved id 'pit-does-not-exist'",)

--- Crucially: validate() never raises. Ingestion of the rest of the batch continues. ---
  FL-NORTH: OK
  FL-BROKEN: WARNING (orphaned reference)
  bench-7: OK
  bench-orphan: WARNING (orphaned reference)
processed all 4 entities without a single exception raised
```

The last block is the design rule in action: one orphaned reference in a batch is
a *warning*, and the other three entities process normally. This is the same
"qualify, don't halt" philosophy `core.CompositeValidator` embodies - and indeed
`OntologyValidator` **is** a `core.BaseValidator` returning a `core.ValidationResult`.

## 9. Repository example reuse

The three `ontology` example scripts were each executed for this tutorial
(exit `0`) and their output pasted above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_equipment_modelling.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/01_equipment_modelling.py) | `RigidHaulTruck`, `HydraulicShovel`, `OperationalState`, `Fleet`, `EntityTypeMetadata`, `to_schema()` | §8.1 |
| [`02_structural_modelling.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/02_structural_modelling.py) | `Mine`, `Pit`, `Bench`, `Shift`, `Relationship`, `RelationshipKind`, `KnowledgeGraphProjection`, `GraphNode`, `GraphEdge`, `BaseEntityType` | §8.2 |
| [`03_validation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/03_validation.py) | `OntologyValidator`, `OntologyValidationError`, `Pit`, `Fleet`, `Bench` | §8.3 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **`Mine(commodity_code=...)`** | `TypeError` - the field is plural | `Mine(id=, commodity_codes=("copper",), method="open_pit")` |
| **`RelationshipKind.PART_OF` for Bench→Pit** | Wrong edge kind (PART_OF is Truck→Fleet) | `RelationshipKind.BELONGS_TO` for Bench→Pit |
| Nesting entities (`bench.pit = pit`) | Reintroduces object-graph coupling; breaks independent serialization | Declare a `Relationship` edge (AD-ON-02) |
| Skipping `@register_equipment` on a new leaf | The type is invisible to `OntologyValidator` and `to_schema()`'s cache | Always register (import-time) |
| Raising on the first `OntologyValidator` warning | Defeats the point - one orphan halts the whole batch | Accumulate `result.errors`, keep processing |
| Defining a new closed taxonomy in `events` | `events` becomes de-facto owner of domain vocabulary | Put governed taxonomies in `ontology` (AD-ON-03) |
| Treating `OperationalState` as live state | It is descriptive metadata, not a mutable field | Current state is a `digital_twin` projection (AD-ON-04) |
| Reaching into `ontology.entity_type._REGISTRY` | Private; may change | Use the type via its `code`; the public registry is `registry`'s job |

## 11. Best practices

- **Model with the types.** A `"haul truck"` string in a column is a bug; there is
  a type for it.
- **Populate `meta` fully**, including `supported_kpis` - a blank field is a
  specification gap, and downstream packages read it.
- **Declare relationships explicitly**; never encode hierarchy in an id naming
  convention only humans can parse.
- **Keep everything UTC** (`Shift.start_utc`/`end_utc`) and use `.contains()`
  rather than re-deriving half-open comparisons.
- **Let contextual validation warn.** Log `result.errors`; never raise on an
  orphaned reference during ingestion.
- **Export `to_schema()`** for integrations instead of hand-writing a JSON contract
  that will drift.

## 12. Performance considerations

- **`to_schema()` is cached per concrete type** after the first call (the shape is
  static for a type version) - repeated exports are free.
- **The type registry is a dict keyed by `code`** - lookup is O(1); registration
  happens once, at import time.
- **`OntologyValidator.validate()` is O(fields)** per entity - it scans the
  candidate's fields once. For a large ingestion batch it is linear in
  entities × fields, with no cross-entity fan-out beyond the injected resolver call.
- **Entities are frozen `slots` dataclasses** (via `core.BaseEntity`) - low memory
  per instance, cheap identity hashing, safe to use as dict keys / set members.
- **`Relationship` edges are plain value objects**, not pointers - a graph of N
  edges is N small frozen objects, trivially serializable and shareable.

## 13. Extension points

`ontology`'s primary extension point is **adding a new entity type** - most often
an **equipment leaf** - with `@register_equipment`, *without editing the package*.
Subclass `EquipmentType`, declare a unique `code`, a fully-populated
`meta: EntityTypeMetadata` (including `supported_kpis`), and any type-specific
`kw_only` fields; the decorator registers it at import. The example below was
executed and passes `ruff` / `ruff format --check` / `mypy --strict`:

```python
import json
from dataclasses import dataclass, field
from typing import ClassVar

from mineproductivity.ontology import (
    EntityTypeMetadata, EquipmentType, Fleet, OntologyValidator, register_equipment,
)


@register_equipment
@dataclass(frozen=True, slots=True, eq=False)
class ElectricRopeShovel(EquipmentType):
    """A large electric rope (cable) shovel for high-volume open-pit loading."""

    code: ClassVar[str] = "ELECTRIC_ROPE_SHOVEL"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Electric Rope Shovel",
        description="A cable-operated electric mining shovel for high-volume open-pit loading.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "LOAD.Rate", "HAUL.MatchFactor"),
    )

    model: str = field(default="", kw_only=True)
    dipper_capacity_m3: float = field(default=0.0, kw_only=True)
```

Exercising it - the new leaf behaves like a built-in one, and registration makes
it resolvable by `OntologyValidator` and exportable via `to_schema()`:

```text
--- The new leaf behaves exactly like a built-in one ---
id=RS-1 code=ELECTRIC_ROPE_SHOVEL rated_capacity=120.0t
shares the inherited state machine: ['operating', 'standby', 'down', 'maintenance']

--- Registration payoff #1: OntologyValidator now resolves its code ---
Fleet referencing 'ELECTRIC_ROPE_SHOVEL': is_valid=True

--- Registration payoff #2: to_schema() exports the new shape ---
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ELECTRIC_ROPE_SHOVEL",
  "type": "object",
  "properties": {
    "rated_capacity": {
      "type": "number"
    },
    "model": {
      "type": "string"
    },
    "dipper_capacity_m3": {
      "type": "number"
    }
  },
  "required": [
    "rated_capacity"
  ]
}
```

Two further extension surfaces use the same "subclass, fill the abstract method"
idiom: a **new sub-ontology family** (new leaves under a new subpackage, added to
`__all__`), and a custom **`KnowledgeGraphProjection`** (implement `nodes()` and
`edges()` - as `02_structural_modelling.py` does) to feed a graph builder from a
different entity set.

!!! note "Ontology extends a frozen lower layer without touching it"
    `BaseEntityType` needed a construction-time `validate()` hook that
    `core.BaseEntity` does not provide. Rather than edit locked `core`, ontology
    **added the hook locally**, mirroring `BaseValueObject`'s pattern. That is the
    template for building on any locked layer: extend upward, never modify
    downward.

## 14. Exercises

1. **Add an equipment leaf.** Following §13, write a `WaterCart` (or any real type
   not already modelled) with its own `code`, `meta.supported_kpis`, and one
   type-specific field. Register it and confirm `OntologyValidator` resolves a
   `Fleet` referencing its code.
2. **Exercise every `RelationshipKind`.** Build a truck, a fleet, an operator, a
   zone, and a cost center, then declare one edge of **each** of the five kinds.
   Which entity is `source_id` and which is `target_id` in each?
3. **Batch validation, no exceptions.** Construct a mixed batch where some entities
   reference unknown type-codes and some reference unresolved ids. Validate all of
   them with one `OntologyValidator`; assert not a single exception was raised and
   collect every warning.
4. **Project a graph.** Implement a `KnowledgeGraphProjection` over a Mine→Pit→Bench
   model plus a fleet, yielding the right `GraphNode`s and `GraphEdge`s. Why can the
   projection never drift from the ontology?
5. **Read the schema.** Export `to_schema()` for two different equipment leaves.
   Which fields are `required`, and why is it always exactly the base-declared
   ones with no default?

## 15. Reference solutions

??? success "Solution 1 - Add an equipment leaf"
    ```python
    @register_equipment
    @dataclass(frozen=True, slots=True, eq=False)
    class WaterCart(EquipmentType):
        code: ClassVar[str] = "WATER_CART"
        meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
            name="Water Cart", description="Towed water cart for dust suppression.",
            supported_kpis=("UTIL.PA", "UTIL.UA"),
        )
        capacity_litres: int = field(default=0, kw_only=True)

    OntologyValidator().validate(
        Fleet(id="FL-W", mine_id="m", equipment_type_code=WaterCart.code)
    ).is_valid  # True
    ```

??? success "Solution 2 - Every RelationshipKind"
    ```python
    Relationship(source_id="HT-214", kind=RelationshipKind.PART_OF,     target_id="FL-NORTH")
    Relationship(source_id="HT-214", kind=RelationshipKind.OPERATED_BY, target_id="OP-1")
    Relationship(source_id="HT-214", kind=RelationshipKind.LOCATED_AT,  target_id="ZONE-DUMP-3")
    Relationship(source_id="BENCH-7", kind=RelationshipKind.BELONGS_TO, target_id="PIT-WEST")
    Relationship(source_id="CC-1",   kind=RelationshipKind.SCOPED_TO,   target_id="BU-COPPER")
    ```
    `source_id` is always the *dependent/child* entity; `target_id` the thing it
    belongs to, is part of, is operated by, is located at, or is scoped to.

??? success "Solution 3 - Batch validation, no exceptions"
    ```python
    resolver = OntologyValidator(entity_resolver=lambda i: i in {"pit-west"})
    batch = [good, unknown_type_code_entity, orphaned_id_entity]
    warnings = []
    for e in batch:                      # no try/except needed - validate never raises
        r = resolver.validate(e)
        if not r.is_valid:
            warnings.extend(r.errors)
    # every entity processed; `warnings` holds all accumulated messages
    ```

??? success "Solution 4 - Project a graph"
    Implement `nodes()`/`edges()` yielding `GraphNode`/`GraphEdge` from the live
    entities and `Relationship`s (see `02_structural_modelling.py`). It cannot
    drift because the projection is *computed from* the same entities and edges the
    ontology holds - there is no second, hand-maintained copy of the graph to fall
    out of sync.

??? success "Solution 5 - Read the schema"
    `required` is always exactly the fields declared with **no default**. On
    `EquipmentType`, `rated_capacity` is the only such field (leaves add their
    fields as `kw_only` *with* defaults), so every equipment leaf's schema requires
    just `rated_capacity`. Change a leaf field to have no default and it joins
    `required` automatically - the schema is derived, not hand-written.

## 16. Further reading

- **[`ontology` package guide](../../packages/ontology.md)** - the capability-tour view.
- **[`ontology` API reference](../../api-reference/ontology.md)** - every symbol, from source.
- **[Ontology Framework Design Specification](../../architecture/02_Ontology_Framework_Design_Specification.md)** - AD-ON-02 (edges not nesting), AD-ON-03 (taxonomy ownership), AD-ON-04 (state is a twin concern), §19 (validation at construction).
- **[Package Tutorial 1 - Core](01_core.md)** · **[Fundamentals L05 - Ontology](../fundamentals/05_ontology.md)** - the layers this tutorial builds on.

---

**Next package tutorial:** Events (deep) - the immutable system of record that
records facts *about* the entities modelled here.
*(Not yet written - Tutorial 3 of 13.)*
