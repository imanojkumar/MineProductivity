# mineproductivity.digital_twin

## Purpose

State representation and synchronization for the live digital twin of mining assets and processes, built as a projection of the event stream — the platform's stateful representation layer, sitting directly above `decision`. A `Twin` is a versioned, registered, identity-bearing object whose state is a provable projection of the event log: `kpis` computes a metric, `analytics` characterizes a series, `decision` recommends an action — `digital_twin` holds the continuously-updated virtual counterpart those computations describe, and keeps it synchronized from `events`' immutable log.

## Scope

**What belongs here:**
- Twin state model interfaces and synchronization contracts.
- Projection interfaces from `events`/`kpis`/`analytics`/`decision` into twin state.

**What must never belong here:**
- Raw connector ingestion (see `connectors`).
- Decision/recommendation logic (see `decision`).
- KPI formulas, statistical computation, optimization search, AI-agent reasoning, or a concrete simulation solver — consumed or interfaced, never re-implemented (design spec §3, §14).

## Responsibilities

- Implements the `digital_twin` subsystem as defined in the Reference Implementation Blueprint v1.0 — the complete design spec §6 module list, in one implementation phase. `Twin` (§8) is the first central abstraction in the series to be entity-shaped rather than stateless: it subclasses `core.BaseEntity[str]` by literal inheritance (identity-based equality inherited unchanged), and representing a state change means producing a new instance via `with_state()`, never mutating in place — `core.BaseEntity`'s own documented contract, applied rather than reinvented. `TwinContext` (§8) carries `kpis.KPIResult`/`analytics.AnalyticsResult`/`decision.DecisionResult` evidence exactly as those packages define it — read, never re-derived (§3.2, the package's single most important boundary). The eleven category base classes (§9) contribute namespace/category-conformance checks only (enforced at class-definition time via `__init_subclass__`, mirroring `kpis`' nine category bases). `TwinStatus` (§10) is the instance's operational lifecycle — `Retired` is terminal and enforced by `TwinSynchronizer`. `TwinSynchronizer`/`SyncPolicy` (§11, §15) orchestrate updates through `events.EventBus.subscribe`/`EventStore.replay`/`EventStore.query` verbatim — cold-start replay and incremental synchronization provably converge on the same `TwinState`; repeated `_apply` failures mark a twin `Degraded` per §10's state diagram. `TwinState` (§12) carries an open, documented `attributes` mapping plus its own `schema_version` (§21's third, per-value versioning axis); `TwinSnapshot` (§13) pairs state with `events.AsOf` for audit/replay/simulation-forking use — deliberately distinct from `events.EventSnapshot`. `TwinSimulationModel` (§14) is an interface-only ABC with zero concrete subclasses by design (ADR-0008's most seriously debated alternative) — the twin-state-level half of the bridge whose business-decision-level half is `decision.WhatIfEngine`. `TelemetryReading` (§16) shapes already-event-sourced sensor readings; it is not a second ingestion boundary parallel to `connectors.FMSConnector`. `by_category`/`by_scope` (§18) are plain `core.PredicateSpecification` factories composed with `TwinRepository.list()`. `TwinRepository` (§20) is a literal `type` alias over `core.BaseRepository[Twin, str]` — the strongest reuse in the series; the reference implementation is `core.InMemoryRepository`, unchanged, with zero new persistence code. `TwinStateCache` (§22) caches evidence *inputs* per `(twin_id, as_of)` — never the twin itself; the repository is always the sole authority for current state. `REGISTRY`/`register` (§17) specialize `registry.Registry` exactly as `decision._registry`/`analytics._registry`/`kpis._registry` do.

## Contents

- `__init__.py` — public API surface (36 symbols, the full design spec §7 list).
- `abstractions.py` — `Twin` (ABC, `core.BaseEntity[str]`), `TwinContext`.
- `metadata.py` — `TwinMetadata`, `TwinCategory`.
- `categories.py` — the eleven twin category base classes.
- `lifecycle.py` — `TwinStatus`.
- `state.py` — `TwinState`.
- `snapshot.py` — `TwinSnapshot`.
- `synchronization.py` — `TwinSynchronizer`, `SyncPolicy`.
- `telemetry.py` — `TelemetryReading`.
- `simulation.py` — `TwinSimulationModel` (ABC, interface only — zero concrete subclasses).
- `discovery.py` — `by_category()`, `by_scope()` specification factories.
- `persistence.py` — `TwinRepository` (`type` alias over `core.BaseRepository[Twin, str]`).
- `caching.py` — `TwinStateCache`.
- `result.py` — `TwinResult` (base), `SyncResult`, `TwinSimulationResult`.
- `_registry.py` — `REGISTRY`, `register`.
- `exceptions.py` — the package's exception hierarchy.
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `events`, `registry`, `kpis`, `analytics`, `decision` (currently exercised); `ontology`, `plugins`, `connectors` are permitted under the platform-wide layering rule — `ontology` supplies the vocabulary a twin's `scope` is expressed in (its entity ids appear as `scope` values rather than as imported types), `plugins` orchestrates entry-point discovery at the application level, and `connectors` is deliberately never exercised: by the time data reaches `digital_twin` it has already been normalized into `events.BaseEvent` subtypes by the `connectors` → `events` pipeline (design spec §5, §16).

**Depended on by:** `simulation`, `optimization`, `agents`, `visualization`

## Future Work

`digital_twin` is feature-complete per the Reference Implementation Blueprint's design spec §6 module list. Future work is limited to: a concrete `TwinSimulationModel` plugin (first-party or third-party, per §27.2 — deliberately never shipped inside this package itself, §31; most plausibly from a future `simulation` package, which is also positioned to become the first concrete implementer of `decision.WhatIfEngine` by composing the two, §14), new twin categories/types (a governance-reviewed `TwinCategory` member plus a category base, §27.1), a production-grade `TwinRepository` backend implementing `core.BaseRepository[Twin, str]` directly (§27.4), and whatever `simulation`/`optimization`/`agents`/`visualization` need from this package as those packages move from architecture-complete to implemented (§34).

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/08_Digital_Twin_Design_Specification.md`](../../../docs/architecture/08_Digital_Twin_Design_Specification.md)
- [`docs/adr/ADR-0008-Digital-Twin.md`](../../../docs/adr/ADR-0008-Digital-Twin.md)
