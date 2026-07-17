# Lesson 02 - Entities

## Objective

Model a haul truck that stays the *same truck* after it is refuelled, relocated, reassigned, and rebuilt - and understand why the framework defines equality by identity rather than by field values.

## Prerequisites

- [Lesson 01 - Hello, MineProductivity](01_hello.md)
- Familiarity with Python dataclasses

## Concepts covered

| Concept | Why it exists |
|---|---|
| `core.BaseEntity[TId]` | Some domain objects have a *continuous identity*. HT-214 is HT-214 whether its odometer reads 412,880 km or 413,198 km. |
| Identity-based equality | `__eq__`/`__hash__` come from `id` alone. This is what lets a truck be a dict key, a repository key, and a stable reference across a decade of state changes. |
| Immutability | Entities are frozen. A state change produces a **new instance**, never a mutation. |
| `InMemoryRepository` | Stores instances keyed by identity. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/02_entities/entities.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/02_entities/entities.py)**

```bash
python examples/fundamentals/02_entities/entities.py
```

The declaration that matters:

```python
from dataclasses import dataclass
from mineproductivity.core import BaseEntity

# eq=False is MANDATORY -- see Common mistakes below.
@dataclass(frozen=True, slots=True, eq=False)
class HaulTruck(BaseEntity[str]):
    model: str
    fleet_id: str
    odometer_km: float
    operational_state: str
```

## Expected output

```text
--- 1. Identity is the truck's fleet number, not its condition ---
HT-214: CAT 793F in FL-NORTH @ 412,880 km

--- 2. The truck hauls a shift: new odometer, new state, same truck ---
before: 412,880 km, operating
after : 413,198 km, standby
same truck? truck == after_shift -> True
(identity-based equality: HT-214 is HT-214 regardless of odometer)

--- 3. A different truck with identical specs is NOT the same truck ---
truck == spare -> False  (HT-214 vs HT-215)
hash(truck) == hash(after_shift) -> True
(hashing by id is what lets a truck be a dict key across state changes)

--- 4. Immutability: the original instance is never mutated ---
assignment rejected: entities are frozen; change means a NEW instance

--- 5. A repository stores instances, keyed by identity ---
fleet holds 2 trucks: ['HT-214', 'HT-215']
HT-214 odometer now: 413,198 km
(the repository is keyed by id -- the truck never became a different truck)
```

## Explanation

**Why not just compare fields?**

Consider what a fleet maintenance system must answer: *"has HT-214 exceeded its service interval?"* If equality compared fields, then HT-214-at-412,880-km and HT-214-at-413,198-km would be two different trucks. Your dictionary of trucks would grow a new entry every shift. Your service history would fragment.

Conversely, two brand-new CAT 793Fs with identical specs, identical odometers, and identical fleet assignments are emphatically **not** the same truck - one of them might be the one with the cracked frame. Field equality would say they are interchangeable. They are not.

So: **identity is the fleet number.** `HT-214 == HT-214` regardless of condition, and `HT-214 != HT-215` regardless of similarity. That is `BaseEntity`.

**Why frozen?**

Because the platform is event-sourced (Lesson 04). If you could mutate a truck's odometer in place, the truck's state would become a side channel that disagrees with the event log. Freezing forces every change through `dataclasses.replace`, producing a new instance - and the repository swap (`remove` then `add`) makes the state transition explicit and auditable rather than invisible.

Notice `hash(truck) == hash(after_shift)` is `True`. Hashing by `id` is precisely what allows the pre-shift and post-shift instances to resolve to the same dictionary slot. This is not an accident; it is the contract.

## Best practices

- **Ask "does this have a continuous identity?"** If yes → entity. If it is a measurement that is interchangeable with any equal measurement → [value object](03_value_objects.md).
- **Use the real-world identifier as `id`.** Fleet number, work order number, shift code. Not a random UUID you invented, if a governed identifier already exists.
- **Model state changes as new instances**, then swap them in the repository. The transition becomes visible.
- **Keep entities small.** They carry identity + state, not behaviour that belongs in a domain service.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **Forgetting `eq=False`** | `@dataclass` silently generates a field-based `__eq__` that **replaces** `BaseEntity`'s identity equality. HT-214 stops equalling HT-214. This is the single most damaging error in this lesson. | `@dataclass(frozen=True, slots=True, eq=False)` - always all three |
| Mutating in place | `FrozenInstanceError`, or (worse, if you unfreeze) state that silently disagrees with the event log | `dataclasses.replace(truck, odometer_km=...)` |
| Using a value object where an entity belongs | Two different trucks compare equal because their specs match | Give it an `id` and subclass `BaseEntity` |
| Generating a random `id` per read | The same physical truck becomes many entities | Use the governed fleet number |

!!! warning "`eq=False` is not optional"
    Python only skips generating a dunder when the **subclass itself** defines it - not when an ancestor does. Omit `eq=False` and your entity quietly loses identity semantics, with no error. Every `BaseEntity` subclass in the framework declares it.

## Exercises

1. **Break it on purpose.** Remove `eq=False` from `HaulTruck` and re-run. Does `truck == after_shift` still hold? Explain precisely why the framework insists on it.
2. **Model an excavator.** Write a `HydraulicShovel(BaseEntity[str])` with `bucket_capacity_m3` and `operating_hours`. Prove that logging 12 hours produces a new instance that still equals the original.
3. **Fleet lookup.** Put five trucks in an `InMemoryRepository` and fetch one by id. Then record a shift for it (replace under the same id) and confirm `len(fleet.list())` did not change.
4. **Think it through.** Is a *shift* an entity or a value object? Is an *ore grade*? Justify each. (Lesson 03 and Lesson 05 will confirm your answer.)

## Suggested next lesson

**[Lesson 03 - Value objects](03_value_objects.md)** - an ore grade of 0.62% Cu has no identity. Any 0.62% is interchangeable with any other. That difference changes how you model it.

---

**See also:** [`core` API Reference](../../api-reference/core.md) · [`core` package guide](../../packages/core.md) · [`core` entity/value-object demo](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/01_entity_and_value_object.py)
