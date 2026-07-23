# Package Tutorial 3 — Events (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 3 of 13"
    Deep, full-surface tutorial for `mineproductivity.events` — the append-only,
    immutable system of record every higher layer projects from. Authored to
    **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.events`: the six canonical event
payloads and the `BaseEvent` contract, the `EventEnvelope` three-timestamp model,
identity/versioning (`EventID`, `EventVersion`) and corrections/idempotency, the
`EventStore` contract and querying (`EventQuery`, `EventFilter`), replay and
time-travel (`AsOf`, `ReplayHandle`, `EventSnapshot`), contextual validation with
confidence scoring, and — the payoff — **defining a new event type** that flows
through the whole machinery unchanged.

All 31 public symbols (`mineproductivity.events.__all__`) are accounted for under
the **coverage convention** (§5): **15 [deep]** (the spine, exercised with executed
output) / **16 [ref]** (the other payloads, the bus, schema, taxonomies, and
exceptions). Public APIs only.

## Prerequisites

- [Package Tutorial 1 — Core (deep)](01_core.md) and
  [Package Tutorial 2 — Ontology (deep)](02_ontology.md): events builds directly on
  **both** (§3).
- [Fundamentals L04 — Events](../fundamentals/04_events.md): the intro — append-only
  facts, three timestamps, why last June's report still reconciles.

This tutorial **builds on** L04; it does not repeat the "why immutable facts"
argument.

## Running the examples

Every code block below is executed and its output pasted verbatim. The three
scripts live in the repository (no extras required):

```bash
pip install -e .
python examples/events/01_first_event.py   # ...and 02, 03
```

---

## 1. Why this package exists

Ontology says *what things are*; something has to record *what happened to them*.
`events` is that record: an append-only, immutable log of facts — a truck
completed a cycle, a shovel went down, a blast was fired. Every layer above is a
*projection* of this log. A KPI is computed from events; a digital twin's live
state is folded from events; an analytics trend reads events. Nothing is stored as
mutable current state — the log is the single source of truth, and everything else
is derived.

Two properties make that safe:

- **Facts are never edited or deleted.** A wrong reading is *corrected* by
  appending a new version, never by overwriting — so last June's report still
  reconciles, and every number traces to an immutable fact with an id and three
  timestamps.
- **The store is a contract, not a database.** `events` defines the `EventStore`
  and `EventBus` *contracts* and ships a private in-memory reference
  implementation for tests and examples; a production backend (an event-sourcing
  database, Kafka) implements the same contract without any layer above noticing.

## 2. Architectural role

`events` sits above `ontology`, below everything that measures or reasons:

```
core ─► ontology ─► events ─► kpis ─► analytics ─► decision ─► digital_twin ─► …
```

It is the hinge of the platform: `ontology` gives events their *vocabulary*
(an event is *about* a `RigidHaulTruck` on a `Bench`), and every intelligence
layer above *consumes* events and re-derives nothing the log already states. When
you see `kpis` compute tonnes-per-hour or a `digital_twin` cold-start from history,
they are reading this package's envelopes.

## 3. Integration with adjacent layers

Events integrates **both** layers below it — the densest integration in the suite.

**Downward to `core` (Tutorial 1) — every building block is a `core` primitive:**

| Events construct | Core primitive it extends / uses |
|---|---|
| `BaseEvent`, `EventEnvelope`, `AsOf`, `ReplayHandle`, `EventSnapshot`, `EventQuery`, `ConfidenceScore`, `ValidationOutcome`, `EventSchema` | subclass `core.BaseValueObject` (immutable, `validate()` on construction) |
| `EventMetadata` | subclasses `core.BaseMetadata` |
| `EventVersion` | subclasses `core.BaseVersionedObject` (`next_version()`, never reset) |
| `EventID` | subclasses `core.BaseIdentifier[str]` (ULID-shaped, time-sortable) |
| `EventStore` | **specializes `core.BaseRepository`** — add→append, plus event-sourcing ops (version-aware `get`, `query`, `replay`) |
| `EventFilter` | a **type alias** for `core.BaseSpecification[EventEnvelope]` — the same `&`/`|`/`~` algebra from Tutorial 1 |
| `EventValidator` | subclasses `core.BaseValidator[BaseEvent]`, returns a `core.ValidationResult` |
| `append()` / `find()` | return `core.Result` / `core.Maybe` |
| the five exceptions | subclass `core.ValidationError` / `NotFoundError` / `MineProductivityError` |

**Downward to `ontology` (Tutorial 2) — events reference and reuse the vocabulary,
never duplicate it:**

- Event payloads carry `equipment_id` / `shift_id` as **references** into the
  ontology (plain strings; ontology owns the entities).
- `SafetyEvent.safety_event_type` is typed by **`ontology`'s `SafetyEventType`** —
  literally the same object (`events.SafetyEventType is ontology.SafetyEventType`).
  `DelayEvent` likewise uses ontology's `DelayCategory` taxonomy. This is design
  spec AD-ON-03 in action: a governed taxonomy lives in `ontology` and its
  consumers reference it rather than each redefining "safety event type".

That is the whole platform discipline in one package: **consume the layers below;
re-derive nothing.**

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| Event payloads | `base_event`, `canonical/` | `BaseEvent`, `CycleEvent`, `ProductionEvent`, `DelayEvent`, `ConsumptionEvent`, `MaintenanceEvent`, `SafetyEvent` |
| Envelope & identity | `envelope`, `identifier`, `versioning` | `EventEnvelope`, `EventMetadata`, `EventID`, `EventVersion` |
| Store & querying | `store` | `EventStore`, `EventQuery`, `EventFilter` |
| Distribution | `bus` | `EventBus`, `Subscription` |
| Replay & time-travel | `replay`, `snapshot` | `AsOf`, `ReplayHandle`, `EventSnapshot` |
| Validation & schema | `validation`, `schema` | `EventValidator`, `ValidationOutcome`, `ConfidenceScore`, `EventSchema` |
| Event taxonomies | `canonical/*` | `ResourceType`, `SafetyEventType` (re-exported from ontology), `SafetySeverity` |
| Exceptions | `exceptions` | `DuplicateEventError`, `EventNotFoundError`, `EventValidationError`, `EventVersionConflictError`, `ReplayError` |

## 5. Public APIs

All 31 exports under the **coverage convention**:

- **[deep]** — taught in a §8 walkthrough with executed output, or in the §13
  extension example.
- **[ref]** — reference coverage: documented in the **"Reference coverage"** table
  below (every symbol named), plus the [API reference](../../api-reference/events.md).

**The spine — [deep]**
: `BaseEvent`, `CycleEvent`, `EventEnvelope`, `EventMetadata`, `EventID`,
  `EventVersion`, `EventStore`, `EventQuery`, `EventFilter`, `EventValidator`,
  `ValidationOutcome`, `ConfidenceScore`, `AsOf`, `ReplayHandle`, `EventSnapshot`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What they model |
|---|---|---|
| Other canonical payloads | `ProductionEvent`, `DelayEvent`, `ConsumptionEvent`, `MaintenanceEvent`, `SafetyEvent` | The other five built-in event types — tonnes moved, a delay (typed by ontology's `DelayCategory`), a resource consumption, a maintenance episode, a safety event (typed by ontology's `SafetyEventType`). Each is a `BaseEvent` exactly like `CycleEvent`. |
| Distribution | `EventBus`, `Subscription` | Near-real-time pub/sub: an `EventStore` calls `EventBus.publish()` after a durable write; `subscribe(filter, handler)` (filter is a `core.BaseSpecification`) returns a `Subscription` you can `cancel()`. Reference: `_InMemoryEventBus`. |
| Schema | `EventSchema` | The machine-readable shape of an event type (`to_json_schema()`), the events-side parity with ontology's `to_schema()`. |
| Taxonomies | `ResourceType`, `SafetyEventType`, `SafetySeverity` | `ResourceType` (FUEL/POWER/WATER/REAGENT) and `SafetySeverity` (LOW→CRITICAL) are events-local enums; `SafetyEventType` is **re-exported from `ontology`** (AD-ON-03). |
| Exceptions | `DuplicateEventError`, `EventNotFoundError`, `EventValidationError`, `EventVersionConflictError`, `ReplayError` | Raised for a rejected duplicate, a missing envelope, a failed structural/schema validation, a version-chain conflict, and an unsatisfiable replay/snapshot request. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. Payload vs envelope.** A `BaseEvent` carries only the business fact
(`equipment_id`, `shift_id`, domain fields) and declares an abstract
`duration_h()`. Identity, version, and the three timestamps live one level up on
`EventEnvelope`. So two different envelopes can wrap field-identical payloads
(two trucks, structurally identical cycles) and still be distinct facts.

**B. Three timestamps, one ordering.** Every envelope carries `event_time_utc`
(when it happened — the calculation basis), `processing_time_utc` (when the source
processed it — diagnostic), and `ingestion_time_utc` (when the platform accepted it
— the audit trail), enforced as `event ≤ processing ≤ ingestion`.

**C. Append-only, corrected by versioning.** The true primary key is
`(EventID, EventVersion)`. `version=1` is the original; a correction is a new
envelope with the **same `EventID`**, `next_version()`, and the same
`event_time_utc`. `get()` returns the latest by default, or any pinned version for
audit. Re-appending an identical envelope is an **idempotent no-op**; a *different*
payload at an existing version is a conflict.

**D. Replay is time-travel over the log.** `replay(AsOf(utc=...))` reconstructs the
logical state (latest version per id) as of a moment; `EventSnapshot` is a
*performance* checkpoint that must never change the *result* of replay.

**E. Validate, then score confidence.** Structural validation raises at
construction. Contextual validation (`EventValidator`) returns a
`ValidationResult` and never raises; `validate_with_confidence()` folds it into a
`ConfidenceScore` — a suspect event is qualified, not discarded.

## 7. Real mining examples

The package is domain-adjacent, so the walkthroughs use its own event types
directly (abbreviated per the template's rule for non-Core packages). The running
model: haul truck `HT-214` on shift `A-2026-06-25` completing `CycleEvent`s across
a shift, one later corrected by a weighbridge, plus a new `BlastEvent` in §13.

## 8. Step-by-step walkthroughs

### 8.1 A first event: construct, validate, envelope, append, query

A `CycleEvent` carries the six cycle segments and a payload; `.cycle_min` and
`.duration_h()` are derived. `EventValidator().validate_with_confidence()` returns
a `ValidationOutcome` (`is_valid` + a `ConfidenceScore`). The event is wrapped in an
`EventEnvelope` (identity via `EventID.generate()`, `EventVersion()`, the three
timestamps, `EventMetadata`), appended to a store (returns a `core.Result`), and
queried back with an `EventQuery`. Running
[`01_first_event.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/01_first_event.py):

```text
--- Construct a CycleEvent ---
cycle_min: 19.5
duration_h: 0.325

--- Contextual validation + confidence scoring ---
is_valid: True, confidence: 1.0

--- Wrap in an EventEnvelope (identity, version, three timestamps) ---
event_id: 01KXVPV7M3WBW66VT4MM5YH76K

--- Append to an EventStore ---
append result -> is_ok: True

--- Query it back ---
found 1 event(s) for HT-214: payload_t=220.0
```

The `event_id` is a 26-character, time-sortable ULID — later ids sort after earlier
ones, a property `EventStore` range-scans rely on. `append` returns a `Result`
(Tutorial 1), not a bare bool: failure is a value you handle, not an exception you
hope to catch.

### 8.2 Replay: time-travel and snapshots

Append three cycles across a shift, each with its own `event_time_utc`, then
`replay(AsOf(utc=...))` reconstructs exactly what had happened as of any moment.
An `EventSnapshot` materializes a checkpoint to accelerate future replay. Running
[`02_replay.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/02_replay.py):

```text
--- Ingesting three cycles across a shift ---
appended cycle at t+0min, payload_t=220.0
appended cycle at t+20min, payload_t=218.0
appended cycle at t+40min, payload_t=225.0

--- Replay at t+15min: only the first cycle had happened ---
1 event(s) visible
  payload_t=220.0

--- Replay at t+60min: all three cycles had happened ---
3 event(s) visible

--- Snapshot: a materialized checkpoint for accelerating future replay ---
snapshot holds 3 event(s) as of its checkpoint
```

Replay at t+15min sees one cycle; at t+60min, three. Nothing was mutated — the log
is identical; only the *as-of point* changed. A snapshot must satisfy an
equivalence law (`replay == fold(query-since-snapshot, snapshot.state)`), so it can
only ever be a speed-up, never a different answer.

### 8.3 Corrections: versioning and idempotency

A weighbridge correction arrives an hour after ingestion. It is a new envelope with
the **same `EventID`**, `EventVersion().next_version()`, and the *same*
`event_time_utc` (the real-world time did not change) — only the payload and the
processing/ingestion times differ. Running
[`03_correction.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/03_correction.py):

```text
--- Original ingestion (version 1) ---
stored payload_t: 220.0

--- A weighbridge correction arrives an hour later ---

--- The current (latest) view resolves to the correction ---
store.get(event_id).payload.payload_t: 214.5

--- The original is still retrievable for audit ---
store.get(event_id, as_of_version=EventVersion()).payload.payload_t: 220.0

--- Re-appending the exact same correction again is idempotent ---
result.is_ok: True (no duplicate created)
```

Three properties in one script: the **current view** resolves to the correction
(214.5); the **original is still there** for audit (`as_of_version=EventVersion()`
pins version 1 → 220.0); and re-appending the identical correction is an
**idempotent no-op** — safe to retry an ingestion without creating duplicates. This
is why the log can be trusted as the record of truth: it never forgets, and it
never double-counts.

## 9. Repository example reuse

The three `events` example scripts were each executed for this tutorial
(exit `0`) and their output pasted above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_first_event.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/01_first_event.py) | `CycleEvent`, `EventValidator`, `ValidationOutcome`, `ConfidenceScore`, `EventEnvelope`, `EventID`, `EventVersion`, `EventMetadata`, `EventQuery` | §8.1 |
| [`02_replay.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/02_replay.py) | `AsOf`, `ReplayHandle`, `EventSnapshot`, `EventEnvelope` | §8.2 |
| [`03_correction.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/events/03_correction.py) | `EventVersion.next_version`, versioned `get`, idempotent `append` | §8.3 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Editing or deleting a stored event to "fix" it | Destroys auditability; historical reports stop reconciling | Append a correction: same `EventID`, `next_version()`, same `event_time_utc` |
| Using `ingestion_time_utc` (or `processing_time_utc`) as the calculation basis | Late-arriving data lands in the wrong shift | Calculate on `event_time_utc` only |
| Timezone-naive datetimes | Comparison/replay bugs at boundaries | Everything UTC and tz-aware |
| Assuming `append` raises on failure | You miss the failure path | It returns a `core.Result` — check `is_ok` / handle `error` |
| Re-appending a *changed* payload at an existing version | `EventVersionConflictError` | Increment the version for a correction; identical re-append is a safe no-op |
| Dropping a low-confidence event | You lose a real (if suspect) fact | Keep it; `EventValidator` **scores** confidence, never discards |
| Redefining a taxonomy (`SafetyEventType`) inside `events` | Duplicates governed vocabulary | Reference `ontology`'s taxonomy (AD-ON-03) |

## 11. Best practices

- **Correct by appending, never by mutating.** The `(EventID, EventVersion)` pair
  is the primary key; corrections increment the version and preserve `event_time_utc`.
- **Compute on `event_time_utc`.** Treat processing/ingestion times as diagnostics
  and audit trail, never as a calculation basis.
- **Make ingestion idempotent.** Identical re-appends are no-ops, so retries are safe.
- **Query with `EventFilter` specifications** (`&`/`|`/`~`) rather than filtering in
  Python after a broad scan.
- **Qualify, don't discard.** Persist events with their `ConfidenceScore`; let
  downstream layers weigh them.
- **Reference ontology's taxonomies**; never redefine a governed enum locally.

## 12. Performance considerations

- **`query()` must be a lazy `Iterator`** (a generator), never a materialized
  `list` — so a store can stream millions of envelopes without loading them all.
- **`EventID` is time-sortable by construction**, so range scans by `event_time_utc`
  can exploit id ordering instead of a full sort.
- **`EventSnapshot` is the performance lever for replay** — it caps how far back a
  cold replay must fold, while (by its equivalence law) never changing the result.
- **`EventFilter` specifications short-circuit** (Tutorial 1) — order the cheapest,
  most selective filter first.
- **Envelopes are frozen `slots` value objects** — cheap to hold in bulk and safe to
  share across a bus's subscribers without defensive copies.

## 13. Extension points

`events`' primary extension point is **defining a new event type** without editing
the package: subclass `BaseEvent`, declare a unique `event_type_code` and the
abstract `duration_h()`, add your domain fields. The new type flows through the
*same* public `EventValidator`, `EventEnvelope`, and `EventStore` — because each
depends on the `BaseEvent` contract, not any concrete type. The example below was
executed and passes `ruff` / `ruff format --check` / `mypy --strict`:

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from mineproductivity.events import (
    BaseEvent, EventEnvelope, EventID, EventQuery, EventValidator, EventVersion,
)
from mineproductivity.events.store import _InMemoryEventStore   # reference store, as in every events example


@dataclass(frozen=True, slots=True)
class BlastEvent(BaseEvent):
    """A production blast fired on a bench -- a fact no canonical type covers."""

    event_type_code: ClassVar[str] = "BLAST"

    bench_id: str = field(default="", kw_only=True)
    holes_fired: int = field(default=0, kw_only=True)
    tonnes_blasted: float = field(default=0.0, kw_only=True)
    clearance_h: float = field(default=0.0, kw_only=True)

    def duration_h(self) -> float:
        return self.clearance_h   # a blast's "duration" is exclusion-zone clearance
```

Exercising it — the custom event flows through the same validator, envelope, and
store, and is queryable by its `event_type_code`:

```text
--- The custom event carries its own fact + shares the contract ---
code=BLAST tonnes_blasted=45000.0 duration_h=1.5

--- It flows through the SAME public validator, unchanged ---
is_valid=True confidence=1.0

--- ...and the SAME envelope + store, unchanged ---
queried by event_type 'BLAST': 1 event(s), bench=bench-7
```

Two further extension surfaces use the same "implement the contract" idiom: a
**custom `EventStore`** (a production event-sourcing backend implementing
`append`/`get`/`find`/`query`/`replay`/`snapshot`) and a **custom `EventBus`** for
real-time distribution — every layer above keeps working, because it depends on
the contract, not your implementation (Dependency Inversion, exactly as Core's
`BaseRepository` in Tutorial 1).

!!! note "The reference store is intentionally private"
    `EventStore` and `EventBus` are abstract contracts; `events` ships *private*
    reference implementations (`_InMemoryEventStore`, `_InMemoryEventBus`) for
    tests and examples, not a public production store. Using `_InMemoryEventStore`
    as a harness — as every events example does — is fine; shipping it as your
    production backend is not what it is for.

## 14. Exercises

1. **Define an event type.** Following §13, write a `TieDownEvent` (or any fact no
   canonical type covers) with its own `event_type_code`, fields, and `duration_h()`.
   Validate it, envelope it, append it, and query it back by `event_type`.
2. **Correct a reading.** Append an event, then append a correction (same `EventID`,
   `next_version()`). Show `get()` returns the correction and
   `get(as_of_version=EventVersion())` returns the original.
3. **Prove idempotency.** Append the *same* envelope twice; assert the store holds
   one fact and both appends report `is_ok`. Then append a *different* payload at the
   same version and observe the conflict.
4. **Replay a shift.** Ingest five cycles at known times; replay at three different
   `AsOf` points and confirm the visible count matches what had happened by each.
5. **Filter with a specification.** Build an `EventFilter` (a
   `core.BaseSpecification[EventEnvelope]`) that matches only high-payload cycles,
   pass it in `EventQuery(filters=...)`, and confirm only those envelopes stream back.

## 15. Reference solutions

??? success "Solution 1 — Define an event type"
    ```python
    @dataclass(frozen=True, slots=True)
    class TieDownEvent(BaseEvent):
        event_type_code: ClassVar[str] = "TIE_DOWN"
        reason: str = field(default="", kw_only=True)
        secured_h: float = field(default=0.0, kw_only=True)
        def duration_h(self) -> float:
            return self.secured_h

    e = TieDownEvent(equipment_id="HT-9", shift_id="B-1", reason="lightning", secured_h=2.0)
    EventValidator().validate(e).is_valid   # True — flows through the same validator
    ```

??? success "Solution 2 — Correct a reading"
    ```python
    eid = EventID.generate()
    store.append(EventEnvelope(event_id=eid, version=EventVersion(), payload=orig, ...))
    store.append(EventEnvelope(event_id=eid, version=EventVersion().next_version(), payload=fixed, ...))
    store.get(eid).payload                      # the correction (latest)
    store.get(eid, as_of_version=EventVersion())  # the original (version 1)
    ```

??? success "Solution 3 — Prove idempotency"
    ```python
    env = EventEnvelope(event_id=eid, version=EventVersion(), payload=p, ...)
    assert store.append(env).is_ok and store.append(env).is_ok   # identical -> no-op
    # a DIFFERENT payload at version 1:
    conflict = store.append(EventEnvelope(event_id=eid, version=EventVersion(), payload=other, ...))
    assert conflict.is_err   # EventVersionConflictError
    ```

??? success "Solution 4 — Replay a shift"
    ```python
    for minute in (0, 10, 20, 30, 40):
        store.append(EventEnvelope(..., event_time_utc=start + timedelta(minutes=minute), ...))
    for cut in (5, 25, 60):
        handle = store.replay(AsOf(utc=start + timedelta(minutes=cut)))
        print(cut, len(handle.envelopes))   # 1, 3, 5
    ```

??? success "Solution 5 — Filter with a specification"
    ```python
    from mineproductivity.core import PredicateSpecification
    heavy: EventFilter = PredicateSpecification(lambda env: env.payload.payload_t >= 220.0)
    heavy_cycles = list(store.query(EventQuery(event_types=("CYCLE",), filters=(heavy,))))
    ```
    `EventFilter` is just `core.BaseSpecification[EventEnvelope]`, so the whole
    `&`/`|`/`~` algebra from Tutorial 1 composes here unchanged.

## 16. Further reading

- **[`events` package guide](../../packages/events.md)** — the capability-tour view.
- **[`events` API reference](../../api-reference/events.md)** — every symbol, from source.
- **[Event Framework Design Specification](../../architecture/01_Event_Framework_Design_Specification.md)** — the three-timestamp model, corrections/idempotency, the snapshot equivalence law.
- **[Package Tutorial 1 — Core](01_core.md)** · **[Package Tutorial 2 — Ontology](02_ontology.md)** · **[Fundamentals L04 — Events](../fundamentals/04_events.md)** — the layers this tutorial builds on.

---

**Next package tutorial:** Registry & Plugins (deep) — the mechanism that turns
every "the platform refuses to choose for you" into an installable extension.
*(Not yet written — Tutorial 4 of 13.)*
