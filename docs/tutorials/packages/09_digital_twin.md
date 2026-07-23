# Package Tutorial 9 — Digital Twin (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 9 of 13"
    Deep, full-surface tutorial for `mineproductivity.digital_twin` — live entity
    state that is **always a projection of the event log**, never a side channel.
    Authored to **Package Tutorial Template v1.0** under the
    [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.digital_twin`: the `Twin` contract
and its eleven `TwinCategory` bases, `_apply`-only state evolution, cold-start via
replay and live `TwinSynchronizer`/`SyncPolicy`, `TwinState`/`TwinSnapshot`,
discovery, and — the payoffs — a **custom `Twin` plugin** and the interface-only
`TwinSimulationModel` hook into simulation.

All 36 public symbols (`mineproductivity.digital_twin.__all__`) are accounted for
under the **coverage convention** (§5): **20 [deep]** / **16 [ref]**. Public APIs
only.

## Prerequisites

- Package Tutorials [1 — Core](01_core.md), [2 — Ontology](02_ontology.md),
  [3 — Events](03_events.md): a twin *is* a `core.BaseEntity`, projects `events`,
  and mirrors `ontology` categories (§3).
- [Fundamentals L09 — Digital Twin](../fundamentals/09_digital_twin.md): the intro —
  state as a projection of the log, and why the absence of a setter is the point.

This tutorial **builds on** L09.

## Running the examples

Every code block below is executed and its output pasted verbatim. Four scripts:

```bash
pip install -e .
python examples/digital_twin/01_provision_and_sync.py   # ...and 02, 03, 04
```

---

## 1. Why this package exists

Everything above `events` needs to answer "what is true *right now*?" — how many
tonnes are on that stockpile, is this conveyor running. The naive answer is a
mutable record someone writes to. This package rejects that: a **`Twin` is an
entity whose state is always a projection of the immutable event log**, reached
only by folding events through `_apply`. There is no setter.

That constraint buys two properties nothing else can: **cold start** (a twin lost
to a restart is reconstructed *exactly* by replaying the log — nothing is stored
anywhere else) and **auditability** (every value traces to the events that produced
it). A single `stockpile.tonnes = 900` written by a well-meaning integration would
destroy both, forever.

## 2. Architectural role

`digital_twin` consumes the log and seeds the projection layers:

```
… events ─► kpis ─► analytics ─► decision ─► digital_twin ─► simulation ─► optimization ─► …
```

It reads `events` to answer "what is true now", and its `TwinSnapshot` is the
*real, evidence-backed starting condition* that `simulation` and `optimization`
project futures from — not a hand-typed guess.

## 3. Integration with adjacent layers

**`events` (Tutorial 3) — the source of truth:** a `Twin`'s only state-changing
method, `_apply(events, *, context)`, folds `BaseEvent`s into a new `TwinState`.
Cold start replays the log; live sync subscribes to the `EventBus` via
`TwinSynchronizer`; `TwinSnapshot` reuses `events.AsOf`. State never comes from
anywhere but the log.

**`ontology` (Tutorial 2):** the eleven `TwinCategory` values (`CONVEYOR`,
`STOCKPILE`, `FLEET`, …) mirror the ontology's equipment/structure families, and a
`Twin` *is* a `core.BaseEntity[str]` exactly as an ontology entity is — same
identity semantics.

**`core` (Tutorial 1):** `Twin` subclasses `core.BaseEntity` (identity equality — a
twin lost and rebuilt is the *same* twin); snapshots serialize via
`core.serialization` generically; discovery composes `core` specifications
(`&`/`|`/`~`).

**`registry` (Tutorial 4):** `REGISTRY` is a `registry.Registry`; `@register`,
`by_category`, and `by_scope` discover twins.

**Upward to `simulation` (Tutorial 10):** `TwinSimulationModel` is the interface-only
contract a future simulation plugin implements, and a `TwinSnapshot` (optionally at
a scenario `AsOf`) is what it seeds from.

## 4. Package structure

| Group | Module(s) | Public symbols |
|---|---|---|
| The twin contract | `abstractions` | `Twin`, `TwinContext` |
| Category bases | `categories/` | `EquipmentTwin`, `ConveyorTwin`, `FleetTwin`, `HaulageTwin`, `MineTwin`, `PlantTwin`, `ProcessingPlantTwin`, `ProductionTwin`, `StockpileTwin`, `GeologicalTwin`, `VentilationTwin` |
| Metadata & lifecycle | `metadata`, `lifecycle` | `TwinCategory`, `TwinMetadata`, `TwinStatus` |
| State & snapshot | `state`, `snapshot`, `caching`, `telemetry` | `TwinState`, `TwinSnapshot`, `TwinStateCache`, `TelemetryReading` |
| Synchronization | `synchronization` | `TwinSynchronizer`, `SyncPolicy` |
| Results | `result` | `TwinResult`, `SyncResult`, `TwinSimulationResult` |
| Persistence & discovery | `persistence`, `discovery`, `_registry` | `TwinRepository`, `by_category`, `by_scope`, `REGISTRY`, `register` |
| Simulation hook | `simulation` | `TwinSimulationModel` |
| Exceptions | `exceptions` | `TwinNotFoundError`, `TwinStateConflictError`, `TwinSyncError`, `TwinValidationError`, `TwinVersionConflictError` |

## 5. Public APIs

All 36 exports under the **coverage convention**:

**The spine — [deep]**
: `Twin`, `TwinContext`, `TwinCategory`, `TwinMetadata`, `TwinStatus`, `TwinState`,
  `TwinSnapshot`, `TwinResult`, `StockpileTwin`, `ConveyorTwin`, `TwinSynchronizer`,
  `SyncPolicy`, `SyncResult`, `TelemetryReading`, `TwinRepository`, `by_category`,
  `by_scope`, `REGISTRY`, `register`, `TwinSimulationModel`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Other category bases | `EquipmentTwin`, `FleetTwin`, `HaulageTwin`, `MineTwin`, `PlantTwin`, `ProcessingPlantTwin`, `ProductionTwin`, `GeologicalTwin`, `VentilationTwin` | The other nine of the eleven `TwinCategory` bases — each a `Twin` subclass you extend exactly as §13 extends one. |
| State & simulation | `TwinStateCache`, `TwinSimulationResult` | A per-twin state cache accelerating repeated reads; the result a `TwinSimulationModel` produces. |
| Exceptions | `TwinNotFoundError`, `TwinStateConflictError`, `TwinSyncError`, `TwinValidationError`, `TwinVersionConflictError` | Unknown twin, a state/version conflict, a sync failure, invalid metadata. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. State is `_apply(events)` only.** A concrete `Twin` declares
`meta: TwinMetadata` and implements `_apply(events, *, context) -> TwinState` — the
*single* way its state changes. No setter exists.

**B. Cold start is free.** Because state lives nowhere but the log, replaying the
relevant events reconstructs a twin *exactly* after any restart — nothing to back
up, nothing to drift.

**C. Live sync is the same fold, incrementally.** A `SyncPolicy` narrows the
`EventBus` to the events a twin reads; `TwinSynchronizer` folds each new event in as
it lands, moving `TwinStatus` PROVISIONED → SYNCHRONIZED.

**D. Identity outlives state.** A `Twin` is a `core.BaseEntity`: the cold-start
instance and the live instance are *equal* (same id) even at different states —
CONV-7 is CONV-7. State changes produce new instances.

**E. A snapshot seeds the layers above.** `TwinSnapshot` freezes "what was true" at
an `AsOf`; simulation and optimization start from it — a real condition, not a
guess. A scenario `AsOf` forks a hypothetical for a `TwinSimulationModel`.

## 7. Real mining examples

The walkthroughs project a conveyor `CONV-7` and a stockpile `SP-1` from the event
log: cold-start + live sync, discovery across categories and pits, snapshot +
round-trip serialization, and a site-pack ventilation twin plugin (§13).

## 8. Step-by-step walkthroughs

### 8.1 Provision, cold-start, and live sync

The log holds CONV-7's history. A `SyncPolicy` filters delivery to the events this
twin reads; cold start replays them into state; then `TwinSynchronizer` takes over
live. The cold-start instance is untouched by later events, yet remains *equal* to
the live one (identity). Running
[`01_provision_and_sync.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/01_provision_and_sync.py):

```text
--- 3. Cold start: reconstruct the twin from genesis via replay ---
replayed 3 relevant event(s) -> tonnes_carried=1197.0

--- 4. Live: subscribe and let TwinSynchronizer take over ---
synchronized: synchronized -> synchronized, events_applied=1
current state: tonnes_carried=1592.0 events_seen=4

--- 5. The twin instance read before the live event is untouched ---
cold-start instance still says: 1197.0
(state changes produce new instances; identity-based equality holds:
 cold-start twin == current twin -> True)

--- 6. Cancelled: later events no longer reach the twin ---
events_seen after cancel: 4
```

### 8.2 Discovery across categories and scopes

`by_category` and `by_scope` find twin instances, and — because they build on
`core` specifications — they compose with `&`/`|`/`~`. A filter matching nothing
returns an empty sequence, never raises. Running
[`02_discovery.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/02_discovery.py):

```text
--- 2. by_category: which twin instances are conveyors? ---
conveyors: ['CONV-7', 'CONV-8']

--- 3. by_scope: everything in the north pit ---
north pit: ['CONV-7', 'SP-1']

--- 4. Composition with the core &/|/~ operators ---
north-pit conveyors: ['CONV-7']
everything else: ['SP-1']

--- 5. A filter matching nothing returns an empty sequence, never raises ---
ventilation twins: []
```

### 8.3 Snapshot, serialize, and seed a fork

`TwinSnapshot` freezes state at an `events.AsOf`; it serializes generically through
`core.serialization` (no bespoke serializer) and round-trips exactly; and a
scenario `AsOf` forks a hypothetical a `TwinSimulationModel` implementer consumes.
Running
[`03_snapshot_and_serialize.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/03_snapshot_and_serialize.py):

```text
--- 2. Capture a point-in-time snapshot (reusing events.AsOf) ---
snapshot of SP-1 as of 2026-07-08 08:00:00+00:00

--- 3. Serialize via core.serialization -- generically, no bespoke serializer ---
twin_id:        SP-1
state:          {'volume_t': 18500.0, 'grade_gpt': 1.42}
schema_version: 1.0.0

--- 4. Round trip: the rebuilt snapshot reproduces state/status/as_of exactly ---
rebuilt == original: True

--- 5. A snapshot can seed a hypothetical fork (scenario AsOf) ---
forked snapshot carries scenario='what-if-reclaim-rate-doubles' -- the hook a future TwinSimulationModel implementer consumes
```

## 9. Repository example reuse

The four `digital_twin` scripts were each executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_provision_and_sync.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/01_provision_and_sync.py) | `Twin`, `ConveyorTwin`, `SyncPolicy`, `TwinSynchronizer`, `SyncResult`, `TwinState`, `TwinStatus` | §8.1 |
| [`02_discovery.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/02_discovery.py) | `by_category`, `by_scope`, `TwinRepository`, `REGISTRY` | §8.2 |
| [`03_snapshot_and_serialize.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/03_snapshot_and_serialize.py) | `TwinSnapshot`, `TwinState`, `TwinResult`, `TelemetryReading` | §8.3 |
| [`04_plugin_twin_type.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/04_plugin_twin_type.py) | `Twin`, `TwinCategory`, `TwinMetadata`, `register` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Adding a state setter | Twin becomes unreconstructable and untraceable — the design collapses | State changes only via `_apply` |
| Persisting twin state as the source of truth | It drifts from the log; cold start disagrees with live | Project from events; replay to cold-start |
| Forgetting the empty-events guard in `_apply` | Needless new state, wrong `captured_at` | `if not events: return self.state` |
| Not filtering with a `SyncPolicy` | Another twin's events land on the wrong instance | Filter delivery with a specification |
| Treating a snapshot as authoritative state | It is a *frozen view*, not the log | The log is truth; a snapshot is a checkpoint |
| Expecting built-in twin types | `digital_twin` ships zero (spec 08 §27) | Define a site-specific `Twin` and register it |

## 11. Best practices

- **Never add a setter.** If you want to write `twin.state[...] = y`, the design is telling you something.
- **Keep `_apply` pure and total** — fold events into a new state; handle the empty case.
- **Filter with a `SyncPolicy`** so a twin only sees the events it projects from.
- **Cold-start from replay** rather than persisting twin state separately.
- **Snapshot before seeding** simulation or optimization.
- **Cancel subscriptions** you no longer need.

## 12. Performance considerations

- **`TwinStateCache`** memoizes a twin's computed state so repeated reads don't
  re-fold; a snapshot caps how far a cold replay must go.
- **A `SyncPolicy` narrows the event stream** at the bus, so a twin folds only its
  own events, not the whole log.
- **Twins are frozen `BaseEntity`s** — cheap identity hashing, safe to share; state
  changes allocate a new instance rather than mutating.
- **Discovery is O(n)** over registered twins, with short-circuiting specifications.

## 13. Extension points — a custom `Twin` (and the simulation hook)

`digital_twin` ships **zero** concrete twin types (spec 08 §27) — a twin type is a
site-specific modelling choice. The extension point is to subclass a category base
(or `Twin`), declare `TwinMetadata`, implement `_apply`, and register — usually as a
plugin. The reused
[`04_plugin_twin_type.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/digital_twin/04_plugin_twin_type.py)
discovers a site-pack ventilation twin through the real entry-point path:

```text
--- 1. digital_twin ships zero built-in twin types ---
registered before discovery: []
(a concrete twin type is a site-specific modeling choice, spec 08 sec. 27)

--- 2. A site pack declares its twin type via a pyproject.toml entry-point ---
discover() -> is_ok: True, loaded entry-points: ('sitepack',)
registered after discovery: ['VENTILATION.SitePackCircuit']

--- 3. The discovered twin type is a first-class, introspectable Twin ---
class=SitePackVentilationTwin category=TwinCategory.VENTILATION

--- 4. ...and provisions/behaves like any built-in would ---
id='VENT-NORTH-1' status='provisioned'
attributes={'airflow_m3s': 210.0, 'ch4_pct': 0.15}
```

The second extension surface is the **interface-only `TwinSimulationModel`**: a
contract (producing a `TwinSimulationResult`) that a future simulation plugin
implements to project a twin's state forward under a hypothesis — seeded from a
`TwinSnapshot`. It ships no implementation, exactly as `analytics.ForecastingModel`
does, because *how* a specific asset evolves is a modelling decision the platform
leaves to you.

!!! note "One projection, many uses"
    A twin's state is a fold of the log; a snapshot freezes it; a
    `TwinSimulationModel` projects it forward. Every one of those is a *view of the
    same events*, never a second, hand-maintained copy that could drift.

## 14. Exercises

1. **Reproject.** Write a `Twin` that tracks *average tonnes per event* instead of the
   total, over the same events. Note you changed the projection without touching a
   single event — why is that powerful?
2. **Prove cold start.** Build a second instance of your twin from scratch and replay
   the same history. Does it reach the same state? Why is that guaranteed?
3. **Time-travel.** Cold-start with an `AsOf` at an earlier moment. What state do you
   get, and why does it differ from the latest?
4. **Break it deliberately.** Add a `set_state()` method. Now answer: how would you
   cold-start after a restart? How would you audit a value? That is the argument for
   the constraint.
5. **Seed a simulation.** Snapshot a twin at a scenario `AsOf` and describe what a
   `TwinSimulationModel` would consume from it. Why a snapshot and not live state?

## 15. Reference solutions

??? success "Solution 1 — Reproject"
    ```python
    class AvgTonnesTwin(ConveyorTwin):
        def _apply(self, events, *, context):
            relevant = [e for e in events if isinstance(e, ProductionEvent)]
            total = sum(e.tonnes_moved for e in relevant)
            n = self.state.attributes.get("n", 0) + len(relevant)
            avg = total / n if n else 0.0
            return TwinState(attributes={"avg_tonnes": avg, "n": n}, ...)
    ```
    You changed the *projection* — the same event log, read differently — without
    editing a single event. Build a second twin tomorrow with different logic and
    replay the same history through it.

??? success "Solution 2 — Prove cold start"
    A fresh instance replaying the same events reaches the identical state, because
    state is a *pure fold of the log* and nothing else. That is the whole guarantee:
    no hidden mutable state to diverge.

??? success "Solution 3 — Time-travel"
    Cold-starting at an earlier `AsOf` folds only the events up to that moment, so you
    see the state as it was then — strictly a prefix of the latest fold.

??? success "Solution 4 — Break it deliberately"
    With a `set_state()`, a restart cannot reconstruct state (it was written out of
    band), and a value cannot be traced to events. Both properties the design exists
    to guarantee are lost — which is exactly why there is no setter.

??? success "Solution 5 — Seed a simulation"
    A snapshot is an immutable, evidence-backed condition at a fixed `AsOf`; a
    simulation needs a *stable* starting point, not a moving live state that changes
    mid-run. The scenario `AsOf` marks it as a hypothetical fork.

## 16. Further reading

- **[`digital_twin` package guide](../../packages/digital_twin.md)** — the capability-tour view.
- **[`digital_twin` API reference](../../api-reference/digital_twin.md)** — every symbol, from source.
- **[Digital Twin Design Specification](../../architecture/08_Digital_Twin_Design_Specification.md)** · **[ADR-0008](../../adr/ADR-0008-Digital-Twin.md)** — projection-from-log, the eleven categories, the no-setter rule (§27).
- **[Fundamentals L09 — Digital Twin](../fundamentals/09_digital_twin.md)** · Package Tutorial [3 — Events](03_events.md).

---

**Next package tutorial:** Simulation (deep) — hypothetical futures over a governed
scenario, seeded from a twin snapshot.
*(Not yet written — Tutorial 10 of 13.)*
