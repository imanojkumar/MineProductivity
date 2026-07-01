# mineproductivity.core

## Purpose

`mineproductivity.core` defines the universal, domain-agnostic framework
primitives that every other MineProductivity package is built on:
entities, value objects, identifiers, metadata, specifications,
repositories, factories, builders, validators, serializers, versioned
objects, configuration, and the `Result`/`Maybe` error-handling types.

It is the first implemented package in this project (v0.2.0) and is held
to the standard of a mature, independently publishable open-source Python
library — comparable in rigor to the foundational modules of NumPy,
Pydantic, or `attrs`.

## Scope

**What belongs here:**

- Base entity/value-object abstractions and identity types.
- Generic, reusable structural patterns from Domain-Driven Design and
  Clean Architecture: Specification, Repository, Factory, Builder,
  Validator, Serializer.
- Domain-agnostic functional error-handling primitives (`Result[T]`,
  `Maybe[T]`) and the shared exception hierarchy.
- Shared typing primitives (`TypeVar`s, `Protocol`s, type aliases) used
  across the rest of the package.

**What must never belong here:**

- Any mining, KPI, event, ontology, equipment, dispatch, connector,
  analytics, optimization, digital twin, decision, or agent concept.
  `core` does not know these domains exist.
- I/O, network, filesystem, or persistence code (that belongs in `io` and
  in concrete repository implementations built on `core.repository`).
- Environment/config *sourcing* (env vars, files, remote config services)
  — `core.configuration` defines the *shape* of configuration; the
  `config` package will decide *where values come from*.
- Anything that imports from any other `mineproductivity` sub-package.
  `core` has zero internal dependencies; this is mechanically verified in
  `tests/unit/core/test_public_api.py::TestPackageVersion::test_core_has_no_dependency_on_sibling_packages`.

## Architecture

`core` has no internal layers of its own — it is the innermost point of
the platform's Clean Architecture, so every module in it sits at the same
depth. What varies is which *pattern family* a module belongs to:

| Family | Modules | Shape |
|---|---|---|
| Identity & state | `entity`, `value_object`, `identifier`, `metadata`, `versioning` | Frozen dataclasses; freely instantiable, meant to be subclassed with domain fields. |
| Structural patterns | `specification`, `repository`, `factory`, `builder`, `validator`, `serialization`, `service` | `abc.ABC` + `@abstractmethod` where a real contract exists; cannot be instantiated directly. |
| Functional core | `result`, `maybe` | Frozen, `Generic[T]` containers; construct via classmethods (`Result.ok`/`.err`, `Maybe.some`/`.nothing`), never the raw constructor. |
| Cross-cutting | `exceptions`, `typing`, `configuration` | Zero or near-zero dependencies; imported from almost every other module. |

A deliberate design split runs through the "Identity & state" family: a
class is a `abc.ABC` with `@abstractmethod` **only** when there is a real,
un-implementable contract (e.g. `BaseRepository.get`). Where a base class
is instead a *data shape* with optional hooks (`BaseValueObject`,
`BaseEntity`, `BaseMetadata`, `BaseVersionedObject`), it is left freely
instantiable — consistent with "no magic": Python's own `abc` machinery
enforces abstractness where it genuinely applies, and nowhere else.

### Internal module dependency graph

```
typing        exceptions        entity        specification        service
  |                |                                                  (leaf)
  |                +---------------------------+
  |                |                           |
  |            value_object                  result
  |            /     |    \                    |
  |     identifier metadata versioning        maybe
  |            |                                |
  |      (leaf modules)                  validator  serialization  configuration
  |                                          (each depends on exceptions,
  |                                           configuration also on value_object)
  |
  +--> factory, builder (depend on result)
  |
  +--> repository (depends on entity, exceptions, maybe, specification)
```

This is a strict DAG — no two modules import each other, directly or
transitively (verified by
`test_public_api.py::TestNoCircularImports`).

## Dependency Rules

```
                     ┌───────────────────┐
                     │   digital_twin     │
                     ├───────────────────┤
                     │     decision       │
                     ├───────────────────┤
                     │     analytics      │
                     ├───────────────────┤
                     │       kpis         │
                     ├───────────────────┤
                     │      events        │
                     ├───────────────────┤
                     │      ontology      │
                     ├───────────────────┤
                     │        core        │   <-- this package
                     └───────────────────┘
```

- **`core` depends on:** nothing in `mineproductivity` — only the Python
  standard library (`dataclasses`, `abc`, `typing`, `uuid`, `types`,
  `collections.abc`).
- **`core` is depended on by:** every other package, directly or
  transitively.
- **Forbidden:** any `from mineproductivity.<other_package> import ...`
  inside `src/mineproductivity/core/`. There is no exception to this
  rule — if a future feature seems to need one, the feature belongs
  outside `core`, not the other way around.
- **Cross-cutting siblings** (`config`, `io`, `utils`, `exceptions`,
  `registry`, `plugins`, `validation`, `cli`) may depend on `core`, and
  `core` intentionally overlaps in *spirit* with a few of them
  (`core.exceptions` vs. the future `exceptions` package,
  `core.validator` vs. the future `validation` package). `core`'s
  versions are the generic, structural mechanism; the sibling packages
  will hold anything that needs to know about more than one package's
  concepts, or needs I/O.

## Public API

Everything below is importable directly from `mineproductivity.core` —
no internal module paths are required:

```python
from mineproductivity.core import (
    # Identity & state
    BaseEntity, BaseValueObject, BaseIdentifier, UUIDIdentifier,
    BaseMetadata, BaseVersionedObject,
    # Structural patterns
    BaseSpecification, AndSpecification, OrSpecification, NotSpecification,
    PredicateSpecification,
    BaseRepository, InMemoryRepository,
    BaseFactory, BaseBuilder, BaseService,
    BaseValidator, CompositeValidator, ValidationResult,
    BaseSerializer, DataclassSerializer, SupportsToDict, SupportsFromDict, to_dict,
    BaseConfiguration,
    # Functional core
    Result, Maybe,
    # Exceptions
    MineProductivityError, ValidationError, ConfigurationError,
    NotFoundError, DuplicateError, SerializationError, BuilderError,
    # Typing
    Comparable, Identifiable, JSONValue, JSONPrimitive,
)
```

`mineproductivity.core.__all__` is the authoritative, sorted list; every
name in it is covered by `test_public_api.py`.

## Extension Guide

**Defining a value object:**

```python
from dataclasses import dataclass
from mineproductivity.core import BaseValueObject

@dataclass(frozen=True, slots=True)
class Money(BaseValueObject):
    amount: int
    currency: str

    def validate(self) -> None:      # optional invariant hook
        if self.amount < 0:
            raise ValueError("amount must be non-negative")
```

**Defining an entity:** always repeat `eq=False` in the subclass
decorator (see [Anti-Patterns](#anti-patterns) below for why):

```python
@dataclass(frozen=True, slots=True, eq=False)
class Truck(BaseEntity[str]):
    model: str
```

**Adding a required field to a class with defaults (`BaseMetadata`,
`BaseVersionedObject`):** their optional fields are declared
`kw_only=True`, so subclasses may freely add required positional fields
without hitting Python's "non-default argument follows default argument"
dataclass restriction.

**Implementing a structural pattern** (`BaseRepository`, `BaseFactory`,
`BaseBuilder`, `BaseValidator`, `BaseSerializer`): subclass and implement
the abstract method(s); the ABC will refuse to instantiate an incomplete
subclass, at import time for you, at runtime for callers.

**Composing instead of subclassing:** prefer `CompositeValidator(...)`
and `spec_a & spec_b & ~spec_c` over writing a new subclass whenever an
existing rule can simply be combined with another.

## Examples

Runnable, narrated scripts live in
[`examples/core/`](../../../examples/core/README.md):

| Script | Demonstrates |
|---|---|
| `01_entity_and_value_object.py` | Identity vs. structural equality, immutability, `replace()` |
| `02_repository.py` | `BaseRepository`/`InMemoryRepository`, specification-based filtering |
| `03_factory_and_builder.py` | `BaseFactory` vs. `BaseBuilder`, `Result`-returning variants |
| `04_validation.py` | `BaseValidator`, `CompositeValidator`, `ValidationResult` |
| `05_serialization.py` | `DataclassSerializer`, `to_dict` |
| `06_result_and_maybe.py` | `Result[T]`/`Maybe[T]` combinators (`map`, `and_then`, `unwrap_or`) |

## Design Rationale

- **Why frozen dataclasses everywhere?** Immutability is the cheapest way
  to make equality, hashing, and thread-safety trivially correct, and it
  is consistent with the platform's event-first architecture, where state
  is always a *projection*, never something mutated in place.
- **Why `kw_only=True` on defaulted base-class fields?** Without it, any
  subclass adding a required field after a base class field with a
  default raises `TypeError: non-default argument follows default
  argument` at class-definition time — a well-known, easy-to-hit
  dataclass inheritance trap. Marking the base's defaulted fields
  keyword-only sidesteps the ordering rule entirely, at zero cost to
  callers (who were already expected to pass those fields by name).
- **Why does `BaseEntity` not override `__repr__`?** Python only skips
  generating a dunder method when the *subclass itself* defines it, not
  when an ancestor does — so a custom `BaseEntity.__repr__` would be
  silently replaced by every concrete subclass's own dataclass-generated
  repr anyway. Leaving `__repr__` to the dataclass machinery gives a more
  useful, full-field repr for debugging, while `__eq__`/`__hash__` (which
  *do* need to be identity-based, not field-based) are defined explicitly
  and subclasses are documented to pass `eq=False` to keep them.
- **Why is `BaseService` not an ABC with abstract methods?** A "service"
  has no universal method signature — forcing one would be exactly the
  kind of "magic"/arbitrary constraint the engineering requirements for
  this package forbid. It exists purely so tooling and readers have a
  common type to recognize "this class is a stateless use-case
  coordinator" by.
- **Why does `Result[T]` fix the error channel to `Exception` instead of
  being doubly generic (`Result[T, E]`)?** PEP 696 (TypeVar defaults),
  which would let `Result[T, E = Exception]` behave ergonomically, is not
  available until Python 3.13. Targeting 3.12, a single type parameter
  with an `Exception`-typed error channel is the simpler, still fully
  useful design; upgrading to a defaulted second type parameter later is
  a backward-compatible addition.
- **Why do `Result`/`Maybe` use private, underscore-prefixed dataclass
  fields instead of a `Union`-based algebraic data type?** A single class
  with classmethod constructors (`Result.ok`/`.err`) is simpler to type,
  pattern-match against with `isinstance`, and document than a two-class
  hierarchy, while `__post_init__` still enforces the "exactly one state"
  invariant that a sealed ADT would give for free.

## Anti-Patterns

Things that look reasonable but are explicitly wrong for this package:

- ❌ **Forgetting `eq=False` on an entity subclass.** `@dataclass` only
  skips generating `__eq__`/`__hash__` when *that exact class* defines
  them; inheriting them from `BaseEntity` is not enough. Omitting
  `eq=False` silently replaces identity-based equality with field-based
  equality — a correctness bug, not a type error, so nothing will warn
  you.
- ❌ **Mutating a `BaseValueObject`/`BaseEntity` field after construction.**
  These are frozen; use `.replace(...)` to get a new instance. If you
  find yourself wanting mutation, the type you're modeling is probably
  not a value object/entity in the DDD sense.
- ❌ **Constructing `Result`/`Maybe` via the raw dataclass constructor**
  (`Result(_value=..., _error=..., _is_ok=...)`). Always use
  `Result.ok`/`Result.err`/`Maybe.some`/`Maybe.nothing`; the
  underscore-prefixed fields are an implementation detail that exists
  only so `dataclasses` can derive equality/hashing for free.
- ❌ **Adding a domain-specific method to a `core` base class** "just this
  once" (e.g. a `TonnesPerHour`-flavored helper on `BaseMetadata`). If it
  mentions a mining concept, it does not belong in `core` — full stop,
  regardless of how small or how convenient.
- ❌ **Reaching for `BaseRepository` when a plain `dict` or `list` would
  do.** The repository pattern earns its complexity when persistence is
  swappable or testable-in-isolation matters; for a throwaway in-memory
  collection inside a single function, it is overkill.
- ❌ **Catching `Exception` instead of `MineProductivityError`** when
  handling framework-raised errors. Every exception `core` raises derives
  from `MineProductivityError` specifically so callers do not need a
  broad `except Exception` to catch framework failures.

## Testing & Quality

- `tests/unit/core/` — one `test_*.py` per source module (see that
  directory's own `README.md`), currently **100% line coverage**, **203
  tests**.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/core/`,
  `tests/unit/core/`, and `examples/core/`.
- The package ships a
  [`py.typed`](../py.typed) marker (PEP 561), so downstream type checkers
  see real types, not `Any`, when importing `mineproductivity`.

## Contents

```
core/
├── __init__.py        # public API surface (__all__)
├── typing.py           # shared TypeVars, Protocols, JSONValue/JSONPrimitive
├── exceptions.py         # MineProductivityError hierarchy
├── value_object.py         # BaseValueObject
├── entity.py                 # BaseEntity
├── identifier.py               # BaseIdentifier, UUIDIdentifier
├── metadata.py                   # BaseMetadata
├── versioning.py                   # BaseVersionedObject
├── specification.py                  # BaseSpecification + And/Or/Not/Predicate
├── result.py                           # Result[T]
├── maybe.py                              # Maybe[T]
├── validator.py                            # BaseValidator, ValidationResult, CompositeValidator
├── serialization.py                          # BaseSerializer, DataclassSerializer, to_dict
├── configuration.py                            # BaseConfiguration
├── factory.py                                    # BaseFactory
├── builder.py                                      # BaseBuilder
├── repository.py                                     # BaseRepository, InMemoryRepository
├── service.py                                          # BaseService
└── README.md                                             # this file
```

## Dependencies

**Depends on:** nothing in `mineproductivity` (leaf package); Python
3.12+ standard library only.

**Depended on by:** every other `mineproductivity` package, per the
dependency direction documented in the root [README.md](../../../README.md#architectural-layering--dependency-direction).

## Future Work

The next packages in the implementation phasing (see
[ROADMAP.md](../../../ROADMAP.md)) will each depend on `core` as follows:

| Future package | Uses from `core` |
|---|---|
| `exceptions` (top-level) | Likely re-homes/extends `core.exceptions`' hierarchy for domain-specific error types. |
| `config` | `BaseConfiguration` as the base for real, environment-sourced settings objects. |
| `ontology` | `BaseEntity`, `BaseValueObject`, `BaseIdentifier`, `BaseMetadata` to model domain concepts. |
| `events` | `BaseValueObject` (immutable event payloads), `BaseIdentifier`, `Result`/`Maybe` for event-store operations. |
| `kpis` | `BaseMetadata` (KPI metadata), `BaseSpecification` (KPI applicability rules), `BaseValidator`. |
| `datasets` | `BaseRepository` for dataset loader contracts, `BaseSerializer` for format adapters. |
| `registry` / `plugins` | `BaseFactory`, `Result` for safe plugin instantiation. |
| every other package | `MineProductivityError` hierarchy, `Result`/`Maybe`, `BaseService`. |

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part I, II
