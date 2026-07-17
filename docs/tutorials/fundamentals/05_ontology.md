# Lesson 05 - Ontology

## Objective

Model equipment, locations, and production time using the platform's shared vocabulary - and understand why two sites that define "haul truck" differently can never compare their tonnes per hour, no matter how good their arithmetic is.

## Prerequisites

- [Lesson 04 - Events](04_events.md) (you now have facts; this lesson is about *what those facts are about*)

## Concepts covered

| Concept | Why it exists |
|---|---|
| Typed equipment leaves (`RigidHaulTruck`, `HydraulicShovel`, …) | A truck is a type with declared capabilities - not a string in a column. |
| Shared base behaviour | Every leaf shares one four-state operational state machine. That is what makes fleet-wide utilisation a coherent question. |
| `meta.supported_kpis` | Metadata declares which KPIs a type can even support. |
| `Mine` → `Pit` → `Bench` | Location is modelled, not implied by a naming convention. |
| `Relationship` + `RelationshipKind` | Explicit typed **edges between ids** - never nested object pointers. |
| `Shift` | Production time is a UTC half-open interval that knows `.contains(t)`. |
| `to_schema()` | Every type exports JSON Schema for dashboards, integrations, and agents. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/05_ontology/ontology.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/05_ontology/ontology.py)**

```bash
python examples/fundamentals/05_ontology/ontology.py
```

Edges, not nesting - this is the design decision worth understanding:

```python
from mineproductivity.ontology import Mine, Pit, Bench, Relationship, RelationshipKind

mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
pit = Pit(id="pit-west", mine_id=mine.id, commodity="copper")
bench = Bench(id="bench-7", pit_id=pit.id, elevation_m=1820.0)

# The Bench does NOT hold a pointer to its Pit. The edge is a separate object.
edges = [
    Relationship(source_id=pit.id, kind=RelationshipKind.BELONGS_TO, target_id=mine.id),
    Relationship(source_id=bench.id, kind=RelationshipKind.BELONGS_TO, target_id=pit.id),
]
```

## Expected output

```text
--- 1. Equipment is a typed leaf, not a string in a spreadsheet ---
HT-214: CAT 793F, rated 226.0t, diesel
SH-1: EX8000, rated 42.0t

--- 2. Shared behaviour lives on the base; specifics live on the leaf ---
operational states (identical for both): ['operating', 'standby', 'down', 'maintenance']
(a truck and a shovel share one state machine -- that is why fleet-wide
 utilisation is even a meaningful question)

--- 3. Metadata declares which KPIs a type can support ---
RigidHaulTruck supports : ('PROD.TruckCycleTime', 'PROD.Payload', 'UTIL.PA', 'UTIL.UA', 'HAUL.TKPH', 'HAUL.MatchFactor')
HydraulicShovel supports: ('UTIL.PA', 'UTIL.UA', 'LOAD.Rate', 'HAUL.MatchFactor')

--- 4. Location and organisation are modelled, not implied ---
bingham-west (open_pit) -> pit-west -> bench-7 @ 1820.0m
fleet FL-NORTH groups equipment_type_code='RIGID_HAUL_TRUCK'

--- 5. Relationships are explicit, typed edges between ids ---
  pit-west --belongs_to--> bingham-west
  bench-7 --belongs_to--> pit-west
  HT-214 --belongs_to--> FL-NORTH
(edges, not nested objects: a Bench does not hold a pointer to its Pit,
 so each entity stays independently serializable -- design spec AD-ON-02)

--- 6. Production time is a modelled interval, not a naive timestamp ---
shift A-2026-06-25 (12.0h) contains 2026-06-25T14:30:00+00:00: True

--- 7. Every type exports its shape as JSON Schema ---
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RIGID_HAUL_TRUCK",
  "type": "object"
}
(dashboards, agents, and integrations read this instead of guessing)
```

## Explanation

**Why an ontology at all?** Because "tonnes per hour" is not a number - it is an *agreement*. If the north pit counts a truck as available while it queues at the shovel and the south pit does not, their availability figures are incomparable. Both are arithmetically flawless. Both are useless side by side.

The ontology is where that agreement is written down in a form a machine can read. Every package above it models the mine using *these* concepts, which is why a KPI computed at one pit means the same thing at another.

**The inheritance split.** Notice section 2: `RigidHaulTruck.operational_states == HydraulicShovel.operational_states`. Common behaviour - the operational state machine, rated capacity - lives on the base `EquipmentType`. Specifics - `fuel_type` on the truck, throughput on the shovel - live on the leaves. This is not tidiness for its own sake: it is precisely what makes "fleet-wide utilisation" a well-defined question across mixed equipment.

**Why `supported_kpis` on the metadata?** Section 3 shows a truck supports `HAUL.TKPH` and a shovel supports `LOAD.Rate`. Asking a shovel for its tonne-kilometres-per-hour is a category error. The metadata makes that checkable *before* someone builds a dashboard that quietly reports zero.

**Edges, not nesting (design spec AD-ON-02).** This is the subtle one. A `Bench` does *not* hold a reference to its `Pit`. Instead a `Relationship` names the two ids and the kind of link. Why? Because nesting would make every entity drag its whole ancestry along - you could not serialize a bench without serializing the mine. With explicit edges, each entity is independently serializable, independently versionable, and the graph is a first-class thing you can query, project, and validate.

**Shift is an interval, not a label.** `shift.contains(probe)` answers "did this happen on A-shift?" without anyone re-deriving a half-open UTC comparison at nineteen call sites, each subtly wrong at the boundary.

## Best practices

- **Model with the ontology's types.** If you find yourself putting `"haul truck"` in a string column, stop - there is a type for it.
- **Check `supported_kpis`** before wiring an equipment type to a metric.
- **Declare relationships explicitly.** Do not encode hierarchy in an id naming convention (`"north-4820"` meaning bench 4820 of the north pit) - that is a convention only humans can read.
- **Everything UTC.** `Shift.start_utc`/`end_utc` are UTC; keep it that way.
- **Export `to_schema()`** for integrations rather than hand-writing a JSON contract that will drift.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **`Mine(commodity_code=..., country=...)`** | `TypeError` - these fields do not exist | `Mine(id=, commodity_codes=("copper",), method="open_pit")` - note the **plural** `commodity_codes` |
| **`RelationshipKind.PART_OF`** | `AttributeError` - this member does not exist | `RelationshipKind.BELONGS_TO` |
| Nesting entities (`bench.pit.mine`) | Entities stop being independently serializable | Declare a `Relationship` edge |
| Encoding hierarchy in ids | Only humans can parse it; machines guess | Explicit edges |
| Assuming a shovel supports truck KPIs | Silent zeros on a dashboard | Check `meta.supported_kpis` |

!!! warning "These two signatures were wrong in this lesson's first draft"
    `Mine(commodity_code=...)` and `RelationshipKind.PART_OF` were both *invented from memory* and both failed at runtime. The real API is `commodity_codes` (plural) and `BELONGS_TO`. This is why the Learning Suite's rule is to read the implementation before writing - see [`examples/ontology/02_structural_modelling.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/ontology/02_structural_modelling.py).

## Exercises

1. **Add a loader.** Construct a `WheelLoader` and compare its `meta.supported_kpis` to the shovel's. Why do they differ?
2. **Extend the graph.** Add a second pit and a second fleet, then write the `Relationship` edges. Print every edge whose `target_id == mine.id`.
3. **Test the boundary.** A shift runs 06:00–18:00 UTC. Does `contains(18:00:00)` return `True`? What does that tell you about half-open intervals, and why does it matter for a cycle recorded at exactly 18:00:00?
4. **Read the schema.** Print the full `truck.to_schema()`. Which fields are required? How would a dashboard use this instead of hard-coding a form?
5. **Explore.** List all 56 ontology exports (`mineproductivity.ontology.__all__`). Find the types for a stope, a conveyor, and a delay category.

## Suggested next lesson

**[Lesson 06 - KPIs](06_kpis.md)** - you have facts (04) about modelled things (05). Now measure them properly, and meet the guardrail that stops the most expensive mistake in mining reporting.

---

**See also:** [`ontology` API Reference](../../api-reference/ontology.md) · [`ontology` package guide](../../packages/ontology.md) · [Ontology Framework design specification](../../architecture/02_Ontology_Framework_Design_Specification.md)
