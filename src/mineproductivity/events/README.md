# mineproductivity.events

## Purpose

`mineproductivity.events` is the immutable, append-only event model every derived state in MineProductivity is computed from: the six canonical event types (`CycleEvent`, `DelayEvent`, `MaintenanceEvent`, `ProductionEvent`, `ConsumptionEvent`, `SafetyEvent`), the `EventStore`/`EventBus` contracts, and the replay/time-travel machinery that makes "recompute, don't trust, a stored number" a first-class operational capability rather than a debugging afterthought.

This package implements the [Event Framework Design Specification](../../../docs/architecture/01_Event_Framework_Design_Specification.md) exactly. Where this README and that specification disagree, the specification governs.

## Scope

**What belongs here:**

- The event contract (`BaseEvent`), envelope, metadata, identity (`EventID`), and versioning (`EventVersion`) types.
- The canonical event type catalogue.
- `EventStore`/`EventBus` interfaces, plus one in-memory reference implementation of each (`_InMemoryEventStore`, `_InMemoryEventBus`) for tests and examples.
- Contextual validation and confidence scoring (`EventValidator`, `ConfidenceScore`).
- Replay/time-travel (`AsOf`, `ReplayHandle`) and snapshotting (`EventSnapshot`).
- Serialization codecs (JSON, Arrow, Parquet) implementing `core.BaseSerializer`.

**What must never belong here:**

- Concrete connector implementations that produce events (see the future `connectors` package — this package defines what a connector must *produce*, never how to read a source).
- KPI computation logic that consumes events (see the future `kpis` package).
- Ontology entity *definitions* (equipment types, locations, organizations) — this package only *references* them by string id, with the sole, minimal exception of `ontology.DelayCategory` (see [Documentation Governance Rule #005](#documentation-governance-rule-005) below).
- A concrete production storage/broker backend (a specific database, message queue client) — `EventStore`/`EventBus` are interfaces; concrete backends belong in `io`/`connectors`.

## Architecture

`events` implements **Event Sourcing**: the event log is the single system of record; every other piece of derived state is a pure function of the event log up to some point in time.

```
core  →  ontology  →  events  →  kpis  →  ...
```

Two lifecycles govern every stored fact:

1. **The envelope lifecycle** (identical for every event, regardless of type): `Produced → Validated → ConfidenceScored → Enveloped → Appended → Published`. Once `Appended`, an envelope is immutable for the rest of its existence.
2. **The version lifecycle** (per `EventID`): `v1 → v2 → v3 → ...`, monotonic, never reset. A correction never mutates a stored envelope — it produces a brand-new envelope with the same `EventID` and an incremented `EventVersion`.

See the [design specification's §11–§14](../../../docs/architecture/01_Event_Framework_Design_Specification.md) for the full state machines, sequence diagrams, and class diagrams.

### Documentation Governance Rule #005

`events.DelayEvent.delay_category` is typed against `ontology.DelayCategory`, an enum the Ontology Framework (a future package) owns. Since the full Ontology Framework has not been implemented yet, only this one minimal shared contract — a closed, six-value enum with no behavior beyond a `precedence` property — has been published ahead of schedule, at `src/mineproductivity/ontology/reference/delay_taxonomy.py`. No other ontology concept (entity types, registry, relationships, reasoning) exists yet. See `ontology/README.md` for the full governance note.

## Package Structure

```
events/
├── __init__.py            # public API surface (__all__)
├── envelope.py              # EventEnvelope, EventMetadata
├── identifier.py              # EventID (ULID-backed)
├── versioning.py                # EventVersion
├── base_event.py                  # BaseEvent (abstract root)
├── schema.py                        # EventSchema
├── canonical/                         # the canonical event type catalogue
│   ├── cycle_event.py                   # CycleEvent
│   ├── delay_event.py                   # DelayEvent
│   ├── maintenance_event.py             # MaintenanceEvent
│   ├── production_event.py              # ProductionEvent
│   ├── consumption_event.py             # ConsumptionEvent, ResourceType
│   └── safety_event.py                  # SafetyEvent, SafetyEventType, SafetySeverity
├── validation.py                        # EventValidator, ConfidenceScore, ValidationOutcome
├── store.py                               # EventStore, EventQuery, EventFilter, _InMemoryEventStore
├── bus.py                                   # EventBus, Subscription, _InMemoryEventBus
├── replay.py                                  # AsOf, ReplayHandle
├── snapshot.py                                  # EventSnapshot
├── serialization/                                 # format codecs
│   ├── json_codec.py                                # JSONEventCodec (no extra dependency)
│   ├── arrow_codec.py                                 # ArrowEventCodec (optional pyarrow)
│   └── parquet_codec.py                                 # ParquetEventCodec (optional pyarrow)
├── exceptions.py                                          # the events exception hierarchy
└── README.md                                                # this file
```

## Dependency Rules

```
core  →  ontology  →  events
```

- **`events` depends on:** `core` and `ontology` (only `DelayCategory` — see above). No other package.
- **`events` is depended on by:** `connectors` (produces events), `kpis` (consumes events), and transitively `analytics`, `decision`, `digital_twin`.
- **Forbidden:** `events` must never import `connectors`, `kpis`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`. This is mechanically checked by `tests/unit/events/test_public_api.py::TestNoForbiddenDependencies`.

## Public API

```python
from mineproductivity.events import (
    # Identity & envelope
    EventID, EventVersion, EventMetadata, EventEnvelope,
    # Base contract
    BaseEvent,
    # Canonical catalogue
    CycleEvent, DelayEvent, MaintenanceEvent, ProductionEvent,
    ConsumptionEvent, ResourceType, SafetyEvent, SafetyEventType, SafetySeverity,
    # Schema & validation
    EventSchema, EventValidator, ValidationOutcome, ConfidenceScore,
    # Store & bus
    EventStore, EventQuery, EventFilter, EventBus, Subscription,
    # Replay & snapshotting
    ReplayHandle, EventSnapshot, AsOf,
    # Exceptions
    EventValidationError, EventVersionConflictError,
    DuplicateEventError, EventNotFoundError, ReplayError,
)
```

Serialization codecs (`JSONEventCodec`, `ArrowEventCodec`, `ParquetEventCodec`) are imported from the `mineproductivity.events.serialization` subpackage rather than the top-level namespace, since two of the three require the optional `pyarrow` dependency:

```python
from mineproductivity.events.serialization import JSONEventCodec, ArrowEventCodec, ParquetEventCodec
```

`_InMemoryEventStore` and `_InMemoryEventBus` (in `events.store`/`events.bus`) are reference implementations for tests and examples, not part of the public, versioned API.

## Extension Guide

**Adding a new canonical event type.** Subclass `BaseEvent`, declare a unique `event_type_code`, implement `duration_h()` and (if the type has invariants) `validate()`:

```python
@dataclass(frozen=True, slots=True)
class BlastEvent(BaseEvent):
    event_type_code: ClassVar[str] = "BLAST"
    powder_factor_kg_per_t: float

    def duration_h(self) -> float:
        return 0.0  # instantaneous
```

No existing canonical type is ever edited to add a new one. Register the new type with `EventValidator`'s consumers and, if it needs JSON/Arrow/Parquet support, it already has it — the codecs are generic over any `BaseEvent` subclass reachable through `events.canonical.canonical_event_types()`.

**Implementing a production `EventStore`/`EventBus`.** Implement the ABC in `store.py`/`bus.py` against a real backend (a database, a message broker). Run it against the shared contract test pattern demonstrated by `_InMemoryEventStore`'s own test suite in `tests/unit/events/test_store.py` to prove conformance, especially the idempotency and replay/snapshot-equivalence properties.

**Adding a new serialization format.** Implement `core.BaseSerializer[EventEnvelope]`. If the format requires a heavy optional dependency, follow the `ArrowEventCodec`/`ParquetEventCodec` pattern: import it lazily inside the method body (never at module top-level), and raise a clear `SerializationError` with an install hint if it is missing.

## Examples

Runnable, narrated scripts live in [`examples/events/`](../../../examples/events/README.md):

| Script | Demonstrates |
|---|---|
| `01_first_event.py` | Construct a `CycleEvent`, validate it, wrap it in an envelope, append it, query it back. |
| `02_replay.py` | Ingest across a shift, then reconstruct state at an earlier point in time via `replay()`. |
| `03_correction.py` | Append a correction under the same `EventID` with an incremented `EventVersion`; compare current vs. historical views; idempotent re-append. |

## Design Rationale

- **Why does `EventEnvelope` wrap `BaseEvent` instead of one flat class?** Identity/version/timing concerns (framework) are kept separate from business fields (domain), so a new event type never needs to redeclare identity/timing plumbing.
- **Why ULIDs, not UUID4, for `EventID`?** ULIDs are lexicographically time-sortable — a range-scan-based `EventStore` can retrieve events in approximate time order directly from the identifier. Implemented from the standard library only (`time.time_ns()` + `secrets.token_bytes()` + a Crockford Base32 encoder), so the "essential packaging requirements only" promise for the base install holds.
- **Why three timestamps, all mandatory?** The Learning & Benchmark Suite v1.0 identifies confusing Event Time and Processing Time as "the single most common temporal error in mining analytics." Making all three fields mandatory, with a validated ordering invariant, turns that class of bug into a constructor-time validation failure.
- **Why is `DelayEvent.delay_category` typed against an `ontology` enum instead of a plain string?** The six categories are closed and governed (Developer & Cookbook Guide Part III); an open string field would silently reintroduce the cross-vendor incomparability the canonical taxonomy exists to prevent. See Documentation Governance Rule #005 above for why only this one enum exists ahead of the full Ontology Framework.
- **Why does `EventMetadata.validate()` use `super(EventMetadata, self).validate()` instead of bare `super().validate()`?** `@dataclass(slots=True)` rebuilds the class object (it cannot add `__slots__` to an existing class), which breaks the implicit `__class__` cell a zero-arg `super()` relies on — a genuine, easy-to-hit Python gotcha in exactly this combination (frozen slotted dataclass + inheritance + an overridden method calling its parent). The explicit two-argument form sidesteps it. See `tests/unit/events/test_envelope.py::TestEventMetadata::test_super_validate_actually_runs`, which exists specifically to guard this regression.
- **Why do the Arrow/Parquet codecs JSON-encode `metadata.attributes` instead of passing it through as a native struct column?** An empty (all-rows) `attributes` dict makes Arrow infer a zero-child struct type, which Parquet's writer cannot physically represent (`ArrowNotImplementedError: Cannot write struct type with no child field`). Encoding that one open-ended field as a JSON string column sidesteps the limitation entirely without constraining what callers may put in `attributes`.
- **Why is `_InMemoryEventStore` wired to accept an optional `EventBus` in its constructor, rather than the two being fully independent?** The design specification's sequence diagram shows `EventStore` calling `EventBus.publish()` as the step immediately following a successful durable write (§13.1) — modeling that dependency directly in the reference implementation demonstrates the "publish only after durability is confirmed" rule concretely, not just in prose.

## Anti-Patterns

- ❌ **Mutating a stored envelope.** There is no `EventStore.update()`. A correction is always a new envelope, same `EventID`, incremented `EventVersion`.
- ❌ **Using `processing_time_utc` or `ingestion_time_utc` to compute operating hours or assign shifts.** Always `event_time_utc`.
- ❌ **Materializing `EventStore.query()` into a `list` "just to count them."** `query()` is a generator; a store backing a 50-million-row shift export must not require 50 million objects in memory at once.
- ❌ **Inventing a new `DelayCategory` value "just this once."** The six categories are closed; a genuinely new distinction requires an ontology/governance change, not a silent seventh value.
- ❌ **Catching `Exception` instead of `EventValidationError`/`MineProductivityError`** when handling a rejected event. Every exception this package raises derives from `core.MineProductivityError` specifically so callers do not need a broad `except Exception`.
- ❌ **A future connector importing `kpis` "to double-check a computed value."** `events` (and everything that produces events for it) never imports `kpis`; this is the anti-corruption boundary the whole platform depends on.
- ❌ **Adding a new `@dataclass(slots=True)` subclass in this package that calls bare `super().validate()`.** See the Design Rationale entry above — use `super(ThisClass, self).validate()` explicitly.

## Testing & Quality

- `tests/unit/events/` — one `test_*.py` per source module (mirroring `canonical/` and `serialization/` as subpackages too) — **100% line coverage**, **229 tests**.
- `tests/integration/test_events_pipeline.py` — the full ingest → validate → append → publish → query → replay → serialize pipeline, end to end, with no direct function call bypassing a stage.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/events/`, `tests/unit/events/`, `tests/integration/`, and `examples/events/`.
- Idempotency and the replay/snapshot equivalence law (design spec §17.1) are each covered by a dedicated property-style test, not just incidental coverage.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core`; `ontology` (only `DelayCategory`). Optionally, `pyarrow` (the `events` extra) for `ArrowEventCodec`/`ParquetEventCodec` — imported lazily, never required to `import mineproductivity.events`.

**Depended on by:** the future `connectors` and `kpis` packages, and transitively `analytics`, `decision`, `digital_twin`.

## Future Work

- A production `EventStore` backend (e.g. backed by a columnar lake with the Parquet partitioning layout `ParquetEventCodec.write_partitioned` already demonstrates).
- A production `EventBus` transport (Kafka/MQTT), per the design specification's streaming extension point.
- Additional canonical event types (`BlastEvent`, `SurveyEvent`, `AssayEvent`) as further mining sub-domains are specified.
- Once the full Ontology Framework is implemented, `EventValidator`'s `entity_resolver` hook can be wired to real entity resolution instead of remaining an optional, caller-supplied callback.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/01_Event_Framework_Design_Specification.md`](../../../docs/architecture/01_Event_Framework_Design_Specification.md)
- [`docs/design/01_Event_Implementation_Checklist.md`](../../../docs/design/01_Event_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 5 ("Your First Event")
- Developer & Cookbook Guide Part III, "Canonical Semantics" (the six-category delay taxonomy)
- Learning & Benchmark Suite v1.0, "Temporal Data Philosophy" (the three-timestamp model, idempotency)
