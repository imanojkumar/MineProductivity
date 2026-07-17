# Lesson 03 - Value objects

## Objective

Model measurements - ore grade, truck payload - as objects that are defined entirely by *what they are*, validate themselves on construction, and cannot exist in an impossible state.

## Prerequisites

- [Lesson 02 - Entities](02_entities.md) (you must understand identity-based equality to appreciate the contrast)

## Concepts covered

| Concept | Why it exists |
|---|---|
| `core.BaseValueObject` | Some domain objects have **no identity**. Any 0.62% Cu grade is interchangeable with any other 0.62% Cu grade. |
| Value-based equality | `__eq__`/`__hash__` come from the fields. Two equal measurements *are* the same measurement. |
| `validate()` | Domain rules live **on the object**. An impossible measurement cannot be constructed at all. |
| `replace()` | Change produces a new, re-validated value. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/03_value_objects/value_objects.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/03_value_objects/value_objects.py)**

```bash
python examples/fundamentals/03_value_objects/value_objects.py
```

The rule that matters - the object refuses to exist illegally:

```python
from dataclasses import dataclass
from mineproductivity.core import BaseValueObject, ValidationError

@dataclass(frozen=True, slots=True)
class Payload(BaseValueObject):
    tonnes: float
    rated_capacity_t: float

    def validate(self) -> None:
        if self.tonnes < 0:
            raise ValidationError(f"tonnes must not be negative, got {self.tonnes}")
        if self.tonnes > self.rated_capacity_t:
            raise ValidationError(
                f"payload {self.tonnes}t exceeds rated capacity {self.rated_capacity_t}t"
            )

    @property
    def utilisation(self) -> float:
        return self.tonnes / self.rated_capacity_t
```

Note there is no `eq=False` here - value objects *want* field-based equality.

## Expected output

```text
--- 1. Equality is by value: two 0.62% grades are the same grade ---
face_sample == lab_sample -> True
hash equal -> True
(no identity: a grade is not 'a particular' grade, it IS its value)

--- 2. Self-validating: an impossible measurement cannot be constructed ---
rejected: percent_cu must be within 0-100, got -4.0

--- 3. Domain rules live on the object, not in the caller ---
payload 220.0t on a 226.0t truck
capacity utilisation: 97.3%
overload rejected: payload 245.0t exceeds rated capacity 226.0t

--- 4. Change means replace: the original value is never mutated ---
face_sample.replace(percent_cu=0.58) -> 0.58% Cu
original still: 0.62% Cu
(replace() re-runs validate(), so the new value is legal too)

--- 5. Values compose into richer values, still validated end to end ---
3 loads moved 653t at 96.3% mean capacity utilisation
(every tonne in that total came from an object that proved itself valid)
```

## Explanation

**Entity or value object?** Ask one question: *does this thing have a continuous identity that survives changes to its attributes?*

- **HT-214** does. Refuel it, rebuild it - still HT-214. → **Entity** (Lesson 02).
- **0.62% Cu** does not. There is no "particular" 0.62% grade with a history. A grade *is* its value. → **Value object**.

Getting this wrong is expensive in both directions. If you gave grades identities, two identical assays would compare unequal and your reconciliation would break. If you gave trucks value equality, HT-214 would stop being HT-214 the moment it burned a litre of diesel.

**Why validate on construction?** This is the platform's answer to unit-less floats leaking through the system. A raw `float` of `-4.0` is perfectly valid Python; it is nonsense as a copper grade. By putting the rule inside `validate()`, the *type system itself* enforces the domain: if you are holding an `OreGrade`, it is a legal grade. You never have to defensively re-check it three layers down.

The `Payload` example shows the same idea carrying a *relationship* between fields: 245 t is a perfectly reasonable number of tonnes, and an impossible load for a 226 t CAT 793F. The object knows that; the caller does not have to. Note the healthy load is 220 t on a 226 t truck - **97.3%** capacity utilisation, which is what a well-loaded haul truck actually looks like.

**Why `replace()` rather than mutation?** Section 4 shows `replace()` re-runs `validate()`. This is the critical property: you cannot mutate your way into an illegal state, because there is no mutation - only construction, and construction always validates.

## Best practices

- **Put the domain rule on the object.** If a reviewer has to remember to check a range, the rule is in the wrong place.
- **Model the relationship, not just the field.** `Payload` knows its own rated capacity, so it can reject an overload.
- **Derive, don't store.** `utilisation` is a `@property`, computed from the fields - it can never drift out of sync.
- **Raise `ValidationError`**, the framework's own type, not a bare `ValueError`.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Adding `eq=False` out of habit | You break the whole point - values must compare by value | Only entities use `eq=False` |
| Validating in the caller | The rule is duplicated at every call site and eventually forgotten at one | Put it in `validate()` |
| Passing raw `float` around | `-4.0` copper and a 245 t load on a 226 t truck both sail through | Wrap the measurement in a value object |
| Storing a derived field | `utilisation` drifts when `tonnes` changes | Make it a `@property` |
| Mutating via `object.__setattr__` | Bypasses `validate()` and produces an illegal object | `replace()` |

## Exercises

1. **Model cycle time.** Write a `CycleTime(BaseValueObject)` with the six haul legs (queue, spot, load, haul, dump, return, all in minutes). Add a `total_min` property. Reject any negative leg.
2. **Add a domain rule.** Extend `OreGrade` to reject a grade above 30% Cu as physically implausible for a porphyry deposit - and write the error message so a geologist understands it.
3. **Prove immutability.** Try to mutate a `Payload` directly. Then try via `replace()` with an overloaded value. What stops you in each case?
4. **Decide.** Are these entities or value objects? (a) a shift, (b) a work order, (c) a fuel burn rate in L/h, (d) a bench elevation, (e) a truck operator. Justify each.

## Suggested next lesson

**[Lesson 04 - Events](04_events.md)** - entities and values describe *what things are*. Events record *what happened*, and everything else in the platform is derived from them.

---

**See also:** [`core` API Reference](../../api-reference/core.md) · [`core` package guide](../../packages/core.md) · [`core` validation demo](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/04_validation.py)
