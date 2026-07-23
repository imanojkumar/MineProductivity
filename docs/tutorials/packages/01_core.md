# Package Tutorial 1 - Core (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 1 of 13"
    The **Fundamentals** suite introduced one idea per package. The **Package
    Tutorials** go a layer deeper: the *full public API* of each package, how it
    integrates with the layers below, and the **extension point** you implement
    to make it your own. This first tutorial covers `mineproductivity.core` - the
    substrate every other package is built on. It is authored to
    **Package Tutorial Template v1.0** and is the reference implementation for the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md)
    that governs Tutorials 2-13.

## Objective

Master the working surface of `mineproductivity.core`: the identity/value split
at depth, the four extension contracts (repository, serializer, validator,
specification), the two constructor patterns (factory, builder), the
railway-oriented error types (`Result`, `Maybe`, the exception hierarchy), and -
the payoff - **implementing the `BaseRepository` contract yourself** for a
production backend.

Everything here is a **public API** (`mineproductivity.core.__all__`, 38 symbols).
Every symbol is accounted for under the **coverage convention** (§5): the working
majority gets **deep coverage** (walkthrough + executed example); the cross-cutting
remainder gets **reference coverage** (a one-line "what/when" plus the API-reference
pointer). No private internals are taught except where you *implement* an abstract
method, which is the contract, not an internal.

## Prerequisites

- [Fundamentals L02 - Entities](../fundamentals/02_entities.md): why HT-214 is
  still HT-214 after a rebuild (identity equality).
- [Fundamentals L03 - Value objects](../fundamentals/03_value_objects.md): why an
  ore grade has no identity and cannot exist invalid (structural equality).

This tutorial **builds on** those two; it does not repeat them. If "entity vs
value object" is not yet second nature, read them first.

## Running the examples

Every code block below is executed and its output pasted verbatim. The six
reusable scripts live in the repository:

```bash
pip install -e .
python examples/core/01_entity_and_value_object.py   # ...and 02-06
```

---

## 1. Why this package exists

Every package in MineProductivity - `events`, `kpis`, `analytics`, `agents`, all
of them - needs the same handful of primitives: a way to say "these two objects
are the same thing", a way to store and look objects up, a way to report failure
without guessing, a way to validate. If each package invented its own, the
platform would have fourteen entity models and fourteen error styles, and no two
of them would compose.

`core` exists so there is **exactly one** of each: one identity model
(`BaseEntity`), one immutable-value model (`BaseValueObject`), one repository
contract (`BaseRepository`), one error hierarchy (`MineProductivityError`), one
explicit-failure type (`Result`). It is the vocabulary the rest of the platform
is written in.

Two constraints define it:

- **No domain knowledge.** `core` does not know what a tonne, a truck, or a shift
  is. The example scripts use `Sensor`, `Coordinates`, `Shift` - but those are
  *defined in the examples*, not in `core`. This is why `ontology` (the mining
  vocabulary) sits **above** `core`, not inside it.
- **No I/O.** `core` performs no file, network, or database access. It defines
  the `BaseRepository` and `BaseConfiguration` *contracts*; the actual SQL driver
  or config loader lives in a higher package that depends on `core`.

## 2. Architectural role

`core` is the root of the dependency chain. The locked layer order is:

```
core ─► ontology ─► events ─► kpis ─► analytics ─► decision
      ─► digital_twin ─► simulation ─► optimization ─► agents ─► visualization
```

Everything points *down* to `core`; `core` points at nothing above it. That is
the **Dependency Inversion Principle** in physical form: `core` publishes
abstract contracts (`BaseRepository`, `BaseSerializer`, `BaseValidator`), and the
packages that need concrete behaviour implement those contracts - never the
reverse. A production SQL repository imports `core.BaseRepository`; `core` never
imports the SQL repository.

This is also why `core` is the correct first Package Tutorial: you cannot deeply
understand any layer above until you can read its `core` foundations fluently.

## 3. Integration with adjacent layers

!!! info "Not applicable - `core` is the foundational layer"
    Every other Package Tutorial (2-13) uses this section to show how the package
    **consumes the governed outputs of the layer below without re-deriving them** -
    the platform's central discipline (e.g. `analytics` reads `KPIResult`s and
    never recomputes tonnes ÷ hours). `core` has **no lower dependency**: it is the
    bottom of the stack and imports nothing from the platform. There is therefore
    no downward integration to describe here.

    What integrates *upward*: every package in §2's chain builds on the primitives
    below. When you meet `EventEnvelope` (events), `KPIMetadata` (kpis), or
    `TwinState` (digital_twin), you are looking at a `BaseValueObject`; every
    `*Repository` is a `BaseRepository`; every package's errors derive from
    `MineProductivityError`. Fluency here is what makes those readable.

## 4. Package structure

`core` is one Python package of small, single-responsibility modules. The public
surface is deliberately flat - you import everything from `mineproductivity.core`,
never from a submodule:

| Module | Public symbols | Concern |
|---|---|---|
| `entity` | `BaseEntity` | identity-based equality |
| `value_object` | `BaseValueObject` | structural equality, immutability |
| `identifier` | `BaseIdentifier`, `UUIDIdentifier` | typed identity wrappers |
| `metadata` | `BaseMetadata` | descriptive name/tags/attributes |
| `versioning` | `BaseVersionedObject` | monotonic version for optimistic concurrency |
| `repository` | `BaseRepository`, `InMemoryRepository` | storage contract + reference impl |
| `specification` | `BaseSpecification`, `And/Or/NotSpecification`, `PredicateSpecification` | composable predicates |
| `factory` | `BaseFactory` | one-shot construction |
| `builder` | `BaseBuilder` | fluent step-by-step construction |
| `validator` | `BaseValidator`, `CompositeValidator`, `ValidationResult` | validation-as-object |
| `serialization` | `BaseSerializer`, `DataclassSerializer`, `to_dict`, `SupportsToDict`, `SupportsFromDict` | object ⇄ plain dict |
| `result` | `Result` | success-or-error without raising |
| `maybe` | `Maybe` | value-or-absence without `None` |
| `configuration` | `BaseConfiguration` | immutable validated settings shape |
| `service` | `BaseService` | marker for stateless domain services |
| `exceptions` | `MineProductivityError` + 6 subclasses | one error hierarchy |
| `typing` | `Comparable`, `Identifiable`, `JSONValue`, `JSONPrimitive` | shared structural types |

## 5. Public APIs

All 38 exports, grouped by role. This is the entire surface - if it is not here,
it is not public. Each symbol carries its **coverage convention** tag:

- **[deep]** - taught below with a walkthrough and an executed example.
- **[ref]** - reference coverage: a one-line "what/when" (see "Reference coverage"
  at the end of this section) plus the [API reference](../../api-reference/core.md).

**Domain building blocks** - all **[deep]**
: `BaseEntity`, `BaseValueObject`, `BaseIdentifier`, `UUIDIdentifier`,
  `BaseMetadata`, `BaseVersionedObject`

**Storage & querying** - all **[deep]**
: `BaseRepository`, `InMemoryRepository`, `BaseSpecification`, `AndSpecification`,
  `OrSpecification`, `NotSpecification`, `PredicateSpecification`

**Construction** - all **[deep]**
: `BaseFactory`, `BaseBuilder`

**Validation** - all **[deep]**
: `BaseValidator`, `CompositeValidator`, `ValidationResult`

**Serialization** - all **[deep]**
: `BaseSerializer`, `DataclassSerializer`, `to_dict`, `SupportsToDict`,
  `SupportsFromDict`

**Error handling** - `Result`, `Maybe`, `MineProductivityError`, `ValidationError`,
  `NotFoundError`, `DuplicateError`, `SerializationError` are **[deep]**;
  `ConfigurationError`, `BuilderError` are **[ref]**

**Cross-cutting** - all **[ref]**
: `BaseConfiguration`, `BaseService`, `Comparable`, `Identifiable`,
  `JSONValue`, `JSONPrimitive`

### Reference coverage

The eight **[ref]** symbols are real public API, used mostly *through* other
packages rather than directly in a first Core tutorial. Each in one line:

| Symbol | What / when to reach for it |
|---|---|
| `BaseConfiguration` | Immutable, self-validating settings container; build with `from_mapping(...)`. Sourcing (env/file) belongs to a higher config package - `core` does no I/O. |
| `BaseService` | Marker base for a *stateless* operation that spans several entities/repositories (a DDD "domain service"); declares no abstract methods. |
| `Comparable` | `@runtime_checkable` structural type for anything supporting `<`; lets a generic sort/rank utility accept `core` types and built-ins alike. |
| `Identifiable` | Structural type for anything exposing an `id`; prefer it over importing `BaseEntity` when you only need "has an id", not "is an entity". |
| `JSONPrimitive` | Type alias `str \| int \| float \| bool \| None` - one JSON scalar. |
| `JSONValue` | Recursive alias: a `JSONPrimitive`, or a `list`/`dict` of `JSONValue`. The vocabulary serialization signatures speak. |
| `ConfigurationError` | Raised when configuration data is missing/malformed (e.g. `BaseConfiguration.from_mapping` on a bad mapping). |
| `BuilderError` | For your `BaseBuilder` to raise when asked to `build()` from incomplete/inconsistent state. |

## 6. Conceptual model

Four ideas explain the whole package.

**A. Two kinds of "sameness".** A domain concept either *has an identity that
outlives its state* (an entity - HT-214 is the same truck before and after a
refuel) or *is fully defined by its values* (a value object - the coordinate
`(40.7, -74.0)` is that coordinate, nothing else). `BaseEntity` gives you the
first; `BaseValueObject` the second. Everything else in `core` is built from
these two.

**B. Contracts live here; implementations live above.** `BaseRepository`,
`BaseSerializer`, `BaseValidator`, and `BaseSpecification` are abstract. `core`
ships one reference implementation where a runnable default is genuinely useful
(`InMemoryRepository`, `DataclassSerializer`, `CompositeValidator`) and *nothing
else*. The real backends are your extension points (§13).

**C. Failure is a value, not (only) an exception.** `Result[T]` and `Maybe[T]`
let a function *return* "this failed" or "there was nothing" instead of raising,
so the caller must handle it. When raising is right, every framework exception
derives from `MineProductivityError`, so one `except` catches them all.

**D. Composition over inheritance.** You extend behaviour by *combining objects*,
not subclassing: specifications combine with `&`, `|`, `~`; validators combine
via `CompositeValidator`; serialization is a separate object, not a method bolted
onto the domain type.

## 7. Real mining examples

`core` is domain-free, so a Package Tutorial has to *supply* the mining domain.
Throughout the walkthroughs the mapping is:

| `core` abstraction | Mining instance used below |
|---|---|
| `BaseValueObject` | `Coordinates` (a pit location), `Reading` (a sensor sample) |
| `BaseEntity[str]` | `Asset`, `Sensor`, `HaulTruck` |
| `BaseIdentifier` | a `TruckId` wrapping a string, so it can't be swapped for a `ShiftId` |
| `BaseSpecification` | `IsLowBattery` (a sensor below 20 %) |
| `BaseFactory` / `BaseBuilder` | a `Shift` constructed two ways |
| `BaseValidator` | asset-code rules (non-empty, ≤ 8 chars, alphanumeric) |
| `BaseRepository` (extension) | a status-indexed `FleetRepository` of haul trucks |

## 8. Step-by-step walkthroughs

### 8.1 Identity vs value, at depth

Beyond L02/L03, two subtleties matter.

**The `eq=False` rule is not optional - and not inherited.** `BaseEntity`
defines identity-based `__eq__`/`__hash__`. But Python regenerates `__eq__` for a
dataclass *unless the subclass itself* declares `eq=False`. Inheriting from
`BaseEntity` is not enough - every concrete entity must repeat it:

```python
@dataclass(frozen=True, slots=True, eq=False)   # eq=False is mandatory
class Asset(BaseEntity[str]):
    name: str
    location: Coordinates
```

Omit `eq=False` and your entity silently reverts to *field-based* equality -
two different trucks with the same fields would compare equal, and identity is
lost. This is the single most common `core` mistake (§10).

**Normalize, then validate - automatically.** Every `BaseValueObject` runs two
hooks after construction, in order: `_normalize()` (coerce/defensively-copy
mutable inputs - because the object is frozen, you assign via
`object.__setattr__`) then `validate()` (raise on an invariant breach). You never
call them; `__post_init__` does. `replace()` re-runs both, so a "modified" copy
can never skip validation.

Running [`01_entity_and_value_object.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/01_entity_and_value_object.py):

```text
--- BaseValueObject: equality by value ---
a == b: True  (same coordinates, different instances)
hash(a) == hash(b): True
a.replace(longitude=-73.9) -> Coordinates(latitude=40.7128, longitude=-73.9)
original a unchanged: Coordinates(latitude=40.7128, longitude=-74.006)
invalid coordinates rejected: latitude must be between -90 and 90

--- BaseEntity: equality by identity ---
original == relocated: True  (same id, different location)
original == different_asset: False  (different id)
repr(original): Asset(id='A-1', name='Crusher #1', location=Coordinates(latitude=40.7128, longitude=-74.006))
```

Note line 3: `replace()` returns a *new* object; `original a` is unchanged -
immutability holds. And `original == relocated` is `True` despite a different
location, because identity, not state, defines an entity's equality.

### 8.2 Typed identifiers, metadata, versioning

Passing raw `str` ids around invites bugs - nothing stops you handing a truck id
to a function expecting a shift id. `BaseIdentifier` wraps a raw value in a typed
value object so the type checker catches the mix-up:

```python
@dataclass(frozen=True, slots=True)
class TruckId(BaseIdentifier[str]):
    pass

TruckId("HT-214") == TruckId("HT-214")   # True - identifiers are value objects
str(TruckId("HT-214"))                     # 'HT-214'
```

`UUIDIdentifier` is the ready-made case: `UUIDIdentifier.generate()` for a fresh
v4 UUID, `UUIDIdentifier.from_string(s)` to parse one back.

`BaseMetadata` is the domain-agnostic `name` / `description` / `tags` /
`attributes` container that higher packages *compose into* their own metadata
(this is the platform's "metadata-first" habit). `BaseVersionedObject` adds a
monotonic `version` and a `next_version()` that returns an incremented copy - the
building block for optimistic-concurrency checks. Both are value objects: you
never mutate, you produce a new instance.

### 8.3 The repository contract and specification algebra

`BaseRepository[TEntity, TId]` is a five-method collection contract: `add`,
`get`, `find`, `remove`, `list`, plus `__contains__` for free. `get` raises
`NotFoundError`; `find` returns a `Maybe` instead - *the caller chooses* whether a
miss is exceptional. `add` raises `DuplicateError` on an id clash.

Filtering is where the **Specification pattern** pays off. A `BaseSpecification`
is one business rule as an object, and rules **compose** with operators:

```python
low_or_flagged = IsLowBattery() | IsFlagged()   # OrSpecification
healthy        = ~IsLowBattery()                # NotSpecification
critical       = IsLowBattery() & IsInPit()     # AndSpecification
repo.list(critical)                             # filtered query
```

For a one-off rule that does not deserve a class, wrap a lambda in
`PredicateSpecification(lambda s: s.battery_percent < 20)`. Running
[`02_repository.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/02_repository.py):

```text
total sensors: 3
low battery sensors: ['Vibration B', 'Temperature C']
find('S-1').is_some: True, name: Vibration A
find('does-not-exist') name-or-default: <not found>
adding a duplicate id raised: Entity with id 'S-1' already exists.
getting a missing id raised: No entity found with id 'does-not-exist'.
after remove('S-3'): ['S-1', 'S-2']
```

Line 4 is the pattern to internalize: `find(...).map(lambda s: s.name).unwrap_or("<not found>")`
handles the miss without a single `if` or `try` - the `Maybe` carries the
absence and the combinators thread the happy path.

### 8.4 Factory vs builder - and their `Result` variants

Both encapsulate construction; choose by shape. A **factory** builds in one shot
from keyword arguments (`BaseFactory.create(**kwargs)`). A **builder** builds
step-by-step with fluent chaining (`BaseBuilder`), which reads better when there
are many optional steps. Both offer an exception-free variant -
`create_result(...)` / `build_result()` - that returns a `Result` instead of
raising, capturing an invalid-input error as an `Err`. Running
[`03_factory_and_builder.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/03_factory_and_builder.py):

```text
--- BaseFactory ---
factory.create(...): Shift(crew='Alpha', start_hour=6, duration_hours=10)
invalid input via create_result -> is_err: True, error: start_hour must be in [0, 24)

--- BaseBuilder (fluent chaining) ---
builder chain -> Shift(crew='Night Crew', start_hour=18, duration_hours=12)
invalid build via build_result -> is_err: True
```

### 8.5 Validation as a separate object

A value object validates its *own* invariants in `validate()`. But *contextual*
rules - ones that depend on external state or vary by use case - belong in a
standalone `BaseValidator`, which returns a `ValidationResult` (never raises by
itself). `CompositeValidator(*validators)` merges several rules, **accumulating
all errors** rather than stopping at the first, and `ValidationResult
.raise_if_invalid()` bridges to an exception-based call site. Running
[`04_validation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/04_validation.py):

```text
'TRK001': valid
'' (empty): invalid -> ['must not be empty', 'must contain only letters and digits']
'this-code-is-way-too-long-and-has-dashes': invalid -> ['must be at most 8 characters', 'must contain only letters and digits']

--- raise_if_invalid() for exception-based call sites ---
raised: ValidationError('Validation failed with 2 error(s).', details={'errors': ('must be at most 8 characters', 'must contain only letters and digits')})
```

Two errors on one candidate - that accumulation is the point. An operator fixing
an asset code sees *every* problem at once, not one per attempt.

### 8.6 Serialization, kept out of the domain type

`core` keeps "how to turn this into a dict" *off* the domain object.
`DataclassSerializer(SomeType)` serializes/deserializes any dataclass;
`to_dict(obj)` is the best-effort helper that prefers an object's own `to_dict()`
(the `SupportsToDict` protocol) and otherwise recurses over dataclass fields.
Deserialization failure raises `SerializationError`. Running
[`05_serialization.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/05_serialization.py):

```text
--- DataclassSerializer ---
serialize(reading) -> {'sensor_id': 'S-1', 'value': 42.5, 'unit': 'celsius'}
as JSON -> {"sensor_id": "S-1", "value": 42.5, "unit": "celsius"}
deserialize(payload) -> Reading(sensor_id='S-1', value=42.5, unit='celsius')
restored == reading: True
```

### 8.7 `Result` and `Maybe` combinators

The two railway types share a chainable surface. `Result[T]`: `ok` / `err`,
`is_ok` / `is_err`, `value` / `error` / `unwrap` / `unwrap_or` / `unwrap_or_else`,
and the combinators `map`, `map_err`, `and_then`. `Maybe[T]`: `some` / `nothing`,
`is_some` / `is_nothing`, `unwrap` / `unwrap_or` / `unwrap_or_else`, `map`,
`and_then`, `filter`, and `to_result(error)` to cross over. Running
[`06_result_and_maybe.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/06_result_and_maybe.py):

```text
--- Result[T]: success/failure without exceptions ---
parse_percentage('42.5') -> ok(42.5)
parse_percentage('not-a-number') -> err('not-a-number' is not a number)
parse_percentage('150') -> err(150.0 is out of range [0, 100])
chained map/and_then -> 800.0

--- Maybe[T]: explicit optionality without None ambiguity ---
find_first_over(readings, 50) -> Maybe.some(88.2)
unwrap_or(default) -> 88.2
find_first_over(readings, 1000) -> Maybe.nothing()
Maybe.to_result(...) -> is_err: True, error: no reading exceeded threshold
```

`chained map/and_then -> 800.0` is a whole validated pipeline
(`parse "80" → /100 → *1000`) with no exceptions and no intermediate `if`.

## 9. Repository example reuse

This tutorial reuses the six `core` example scripts rather than inventing new
ones - they are executable documentation, kept correct because they are run. Each
was executed for this tutorial (exit `0`) and its output pasted above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_entity_and_value_object.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/01_entity_and_value_object.py) | `BaseEntity`, `BaseValueObject`, `replace` | §8.1 |
| [`02_repository.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/02_repository.py) | `InMemoryRepository`, `BaseSpecification`, `Maybe`, `DuplicateError`, `NotFoundError` | §8.3 |
| [`03_factory_and_builder.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/03_factory_and_builder.py) | `BaseFactory`, `BaseBuilder`, `Result` variants | §8.4 |
| [`04_validation.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/04_validation.py) | `BaseValidator`, `CompositeValidator`, `ValidationResult` | §8.5 |
| [`05_serialization.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/05_serialization.py) | `DataclassSerializer`, `to_dict` | §8.6 |
| [`06_result_and_maybe.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/core/06_result_and_maybe.py) | `Result`, `Maybe` combinators | §8.7 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **Omitting `eq=False`** on a `BaseEntity` subclass | Identity silently reverts to field equality; two different trucks compare equal | Always `@dataclass(frozen=True, slots=True, eq=False)` |
| Using an entity where a value object belongs (or vice-versa) | Wrong equality semantics; e.g. two equal ore grades treated as distinct | Has an identity that outlives state → entity; else → value object |
| Assigning in `_normalize` with plain `self.x = ...` | `FrozenInstanceError` - the object is frozen | `object.__setattr__(self, "x", value)` |
| Unwrapping a `Result`/`Maybe` without checking | `unwrap()` on an `Err`/`nothing` raises | Check `is_ok`/`is_some`, or use `unwrap_or` / `map` / `and_then` |
| Reading `.error` on an `Ok` (or `.value` on an `Err`) | `ValueError` / the stored exception is raised | Guard with `is_err` / `is_ok` first |
| Deserializing a mapping with the wrong keys | `SerializationError` wrapping the `TypeError` | Serialize/deserialize the *same* dataclass shape |
| Mutating a "changed" value object in place | Impossible (frozen) or, if forced, skips validation | `replace(**changes)` - it re-runs `_normalize`+`validate` |
| Importing from a submodule (`core.entity`) | Brittle to internal moves | Import from `mineproductivity.core` |

## 11. Best practices

- **Declare the identity type.** `BaseEntity[str]` or, better, a
  `BaseIdentifier` subclass - it lets the type checker catch id mix-ups.
- **Put invariants in `validate()`, contextual rules in a `BaseValidator`.** The
  object guards what is *always* true of it; the validator guards what is true
  *in a use case*.
- **Return `Result`/`Maybe` from fallible/optional operations** you expect
  callers to handle in the normal course; reserve raising for genuinely
  exceptional paths.
- **Catch broadly with `MineProductivityError`**, narrowly with a subclass - the
  hierarchy supports both from one `try`.
- **Filter repositories with specifications**, and compose them (`&`, `|`, `~`)
  instead of writing bespoke query methods.
- **Keep serialization in a `BaseSerializer`**, not on the domain type.

## 12. Performance considerations

- **`frozen=True, slots=True` is a performance choice, not just a safety one.**
  `slots` removes the per-instance `__dict__`, cutting memory and speeding
  attribute access - it matters when you hold millions of readings or events.
- **`InMemoryRepository.list(spec)` is O(n)** - it scans and applies the
  specification to every stored entity. It is a reference implementation for
  tests and examples; a production backend should push the predicate down to an
  indexed query (see §13, where the `FleetRepository` keeps a status index for an
  O(1) lookup the base scan cannot match).
- **Specification combinators short-circuit** - `And` stops at the first `False`,
  `Or` at the first `True` - so order the cheap, selective rule first.
- **`Result`/`Maybe` allocate a small frozen object per step.** In a tight inner
  loop over huge sequences, a plain `try`/`for` may be leaner; at API boundaries
  the clarity is worth the allocation.
- **Entity hashing is `hash((type, id))`** - cheap and stable, so entities are
  fine as dict keys and set members.

## 13. Extension points

`core`'s primary extension point is the one the architecture calls out:
**implement the `BaseRepository[TEntity, TId]` contract** for a real backend.
You provide the five methods; every layer above keeps working, because it depends
on the *contract*, not your implementation (Dependency Inversion, made concrete).

The example below is a status-indexed in-memory fleet backend. It implements the
full contract *and* adds a domain query (`by_status`) the base contract does not
define - extension, not modification. It was executed, and passes
`ruff` / `ruff format --check` / `mypy --strict`:

```python
from collections.abc import Sequence
from dataclasses import dataclass

from mineproductivity.core import (
    BaseEntity, BaseRepository, BaseSpecification,
    DuplicateError, Maybe, NotFoundError,
)


@dataclass(frozen=True, slots=True, eq=False)
class HaulTruck(BaseEntity[str]):
    model: str
    status: str  # "hauling" | "queued" | "down"


class FleetRepository(BaseRepository[HaulTruck, str]):
    """Implements the contract, plus a secondary index by status."""

    def __init__(self) -> None:
        self._by_id: dict[str, HaulTruck] = {}
        self._ids_by_status: dict[str, set[str]] = {}

    def add(self, entity: HaulTruck) -> None:
        if entity.id in self._by_id:
            raise DuplicateError(f"Truck {entity.id!r} already exists.")
        self._by_id[entity.id] = entity
        self._ids_by_status.setdefault(entity.status, set()).add(entity.id)

    def get(self, entity_id: str) -> HaulTruck:
        try:
            return self._by_id[entity_id]
        except KeyError as exc:
            raise NotFoundError(f"No truck with id {entity_id!r}.") from exc

    def find(self, entity_id: str) -> Maybe[HaulTruck]:
        truck = self._by_id.get(entity_id)
        return Maybe.nothing() if truck is None else Maybe.some(truck)

    def remove(self, entity_id: str) -> None:
        try:
            truck = self._by_id.pop(entity_id)
        except KeyError as exc:
            raise NotFoundError(f"No truck with id {entity_id!r}.") from exc
        self._ids_by_status[truck.status].discard(entity_id)

    def list(
        self, specification: BaseSpecification[HaulTruck] | None = None
    ) -> Sequence[HaulTruck]:
        trucks = list(self._by_id.values())
        if specification is None:
            return trucks
        return [t for t in trucks if specification.is_satisfied_by(t)]

    def by_status(self, status: str) -> Sequence[HaulTruck]:  # domain extension
        return [self._by_id[i] for i in self._ids_by_status.get(status, set())]
```

Exercising it:

```text
fleet size (inherited list()): 3
down trucks (custom by_status index): ['HT-215', 'HT-216']
get('HT-214').model (inherited): CAT 793
'HT-999' in repo (inherited __contains__): False
duplicate rejected (contract preserved): Truck 'HT-214' already exists.
after remove('HT-215'), down trucks: ['HT-216']
```

The same technique implements the other three contracts: a **`BaseSerializer`**
for a non-dataclass wire format, a **`BaseValidator`** for a contextual rule set,
or a **`BaseSpecification`** for a reusable business rule. Each is "subclass, fill
the abstract method, and everything above composes with it unchanged."

!!! note "Core is not interface-only"
    Unlike `analytics` or `decision` (which ship *zero* implementations of their
    key contract), `core` ships a working `InMemoryRepository`. So extending
    `core` is "provide a production-grade implementation of a contract that
    already has a reference one", not "the platform refuses to choose for you".
    The mechanism - subclass an abstract base - is identical; the intent differs.

## 14. Exercises

1. **Break identity on purpose.** Define a `BaseEntity` subclass *without*
   `eq=False`. Construct two instances with the same fields but different ids and
   compare them. Explain the result, then fix it.
2. **A typed id.** Define `TruckId(BaseIdentifier[str])` and `ShiftId(BaseIdentifier[str])`.
   Write a function annotated to take a `TruckId`; try passing a `ShiftId`. What
   does `mypy` say, and why is that the whole point?
3. **Specification algebra.** Add an `IsDown` and an `IsHeavyHauler` specification
   over the `HaulTruck` above (a heavy hauler being, say, `model == "CAT 793"`),
   build "down **and** a heavy hauler" and "**not** down" with the operators, and
   filter a `FleetRepository` with each.
4. **Railway pipeline.** Write `parse_tonnage(raw: str) -> Result[float]` that
   fails on non-numeric or negative input, then chain `.map`/`.and_then` to
   convert tonnes to a truck-count estimate - with no `try` in the caller.
5. **Implement a second repository.** Write an `AuditingRepository[E, str]` that
   wraps the contract and records every `add`/`remove` to an in-memory log,
   exposing a `history()` method. Which methods must you implement, and which can
   you leave to the pattern?

## 15. Reference solutions

??? success "Solution 1 - Break identity on purpose"
    ```python
    @dataclass(frozen=True, slots=True)   # note: eq=False MISSING
    class Bad(BaseEntity[str]):
        name: str

    Bad(id="A", name="x") == Bad(id="B", name="x")   # True (!) - field equality
    ```
    The dataclass regenerated a field-based `__eq__` on the subclass, shadowing
    `BaseEntity`'s identity one. Add `eq=False` to the decorator and the same
    comparison becomes `False`, because equality is now `(type, id)`.

??? success "Solution 2 - A typed id"
    ```python
    @dataclass(frozen=True, slots=True)
    class TruckId(BaseIdentifier[str]): ...
    @dataclass(frozen=True, slots=True)
    class ShiftId(BaseIdentifier[str]): ...

    def dispatch(truck: TruckId) -> None: ...
    dispatch(ShiftId("A-2026-06-28"))   # mypy: Argument 1 has incompatible type "ShiftId"
    ```
    Both wrap a `str`, but they are distinct types, so the checker rejects the
    swap that a bare `str` would have allowed silently.

??? success "Solution 3 - Specification algebra"
    ```python
    class IsDown(BaseSpecification[HaulTruck]):
        def is_satisfied_by(self, c: HaulTruck) -> bool:
            return c.status == "down"

    class IsHeavyHauler(BaseSpecification[HaulTruck]):
        def is_satisfied_by(self, c: HaulTruck) -> bool:
            return c.model == "CAT 793"

    repo.list(IsDown() & IsHeavyHauler())
    repo.list(~IsDown())
    ```

??? success "Solution 4 - Railway pipeline"
    ```python
    def parse_tonnage(raw: str) -> Result[float]:
        try:
            value = float(raw)
        except ValueError:
            return Result.err(f"{raw!r} is not a number")
        return Result.ok(value) if value >= 0 else Result.err("tonnage must be >= 0")

    trucks = parse_tonnage("612").map(lambda t: t / 200).unwrap_or(0.0)   # 3.06
    ```

??? success "Solution 5 - AuditingRepository"
    You must implement all five abstract methods (`add`, `get`, `find`, `remove`,
    `list`) - `__contains__` comes free from the base. Delegate storage to a
    private `InMemoryRepository`, and append to a log inside `add`/`remove`:
    ```python
    class AuditingRepository(BaseRepository[HaulTruck, str]):
        def __init__(self) -> None:
            self._inner: InMemoryRepository[HaulTruck, str] = InMemoryRepository()
            self._log: list[str] = []

        def add(self, entity: HaulTruck) -> None:
            self._inner.add(entity)
            self._log.append(f"add {entity.id}")

        def get(self, entity_id: str) -> HaulTruck:
            return self._inner.get(entity_id)

        def find(self, entity_id: str) -> Maybe[HaulTruck]:
            return self._inner.find(entity_id)

        def remove(self, entity_id: str) -> None:
            self._inner.remove(entity_id)
            self._log.append(f"remove {entity_id}")

        def list(self, specification: BaseSpecification[HaulTruck] | None = None) -> Sequence[HaulTruck]:
            return self._inner.list(specification)

        def history(self) -> Sequence[str]:
            return tuple(self._log)
    ```

## 16. Further reading

- **[`core` package guide](../../packages/core.md)** - the capability-tour view.
- **[`core` API reference](../../api-reference/core.md)** - every symbol, generated from source.
- **[Architecture Handbook](../../architecture/README.md)** - the locked design specifications and the ADRs behind them.
- **Fundamentals [L02 - Entities](../fundamentals/02_entities.md) · [L03 - Value objects](../fundamentals/03_value_objects.md)** - the first contact this tutorial deepens.

---

**Next package tutorial:** Ontology (deep) - the mining vocabulary that turns
`core`'s domain-free primitives into equipment, material, locations, and shifts.
*(Not yet written - Tutorial 2 of 13.)*
