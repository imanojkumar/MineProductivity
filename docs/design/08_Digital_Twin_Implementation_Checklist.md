# Digital Twin - Implementation Checklist

**Package:** `mineproductivity.digital_twin`
**Governing specification:** [`docs/architecture/08_Digital_Twin_Design_Specification.md`](../architecture/08_Digital_Twin_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0008-Digital-Twin.md`](../adr/ADR-0008-Digital-Twin.md)
**Status:** Not started

Binding, **locked** implementation contract for `digital_twin` - the third package built on top of the Foundation Layer, sitting directly above the now-locked `decision`. Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification (`08_Digital_Twin_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–07.
- [ ] ADR-0008 read in full; the rationale for `digital_twin` existing as a separate, stateful package above `decision` (and for `Twin` subclassing `core.BaseEntity` rather than being a plain mutable object) is understood, not merely accepted.
- [ ] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`, `analytics`, `decision` available and importable, exactly as released; no lower package file is modified as a side effect of this work.
- [ ] Confirmed: `digital_twin` will not import `simulation`, `optimization`, `agents`, or `visualization` under any circumstance - none of those packages exist yet (design spec §5).
- [ ] Confirmed: no lower package (`core` through `decision`) will be modified to import or otherwise reference `digital_twin` (design spec §5, §3.6).

## Package Structure

- [ ] `src/mineproductivity/digital_twin/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `categories.py`, `lifecycle.py`, `state.py`, `snapshot.py`, `synchronization.py`, `telemetry.py`, `simulation.py`, `discovery.py`, `persistence.py`, `caching.py`, `result.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `digital_twin/README.md` written following the `core/README.md` template.
- [ ] Confirmed `simulation.py` contains zero concrete, non-test subclasses of `TwinSimulationModel` (mechanical grep/AST check - design spec §14, §32's interface-purity proof).
- [ ] Confirmed `telemetry.py` contains no direct import of, or reference to, any `connectors`-package class - telemetry integration composes over already-event-sourced data only (design spec §16).

## Public API

- [ ] `digital_twin/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [ ] `TestNoForbiddenDependencies` AST-walks every `digital_twin` submodule for a forbidden import (`simulation`, `optimization`, `agents`, `visualization`) - mirrors every existing package's own copy of this test (design spec §5).
- [ ] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis,analytics,decision}/` imports `mineproductivity.digital_twin` (design spec §5, §3.6) - the `analytics`/`decision`-package precedent for this test (spec 06/07 checklists) extended one layer up.

## Twin Abstractions and Identity (§8, §9)

- [ ] `Twin` (§8) - subclasses `core.BaseEntity[str]` directly; `meta: ClassVar[TwinMetadata]`, `scope: Mapping[str, str]`, `state: TwinState`, `status: TwinStatus`; `_apply()` abstract; `with_state()` non-overridden, produces a new instance via `dataclasses.replace`, never mutates `self`.
- [ ] `TwinContext` (§8) - `event_store`, `kpi_results`, `analytics_results`, `decision_results`, optional `as_of`.
- [ ] Identity/equality proven: `Twin.__eq__`/`__hash__` inherited unchanged from `BaseEntity` (identity-based on `id`, ignoring `state`/`status`); no override anywhere in the package.
- [ ] All eleven twin category base classes (§9) implemented: `MineTwin`, `EquipmentTwin`, `PlantTwin`, `ConveyorTwin`, `HaulageTwin`, `FleetTwin`, `ProcessingPlantTwin`, `GeologicalTwin`, `VentilationTwin`, `StockpileTwin`, `ProductionTwin` - each contributing only a namespace/category-check convention, no additional behavior.
- [ ] Confirmed `scope` is set once at construction and never re-assigned in place anywhere in the codebase (design spec §9, §31's recorded anti-pattern).

## Lifecycle (§10)

- [ ] `TwinStatus` enum (§10) - exactly `Provisioned`/`Synchronized`/`Stale`/`Degraded`/`Retired`.
- [ ] Lifecycle transitions proven to match design spec §10's state diagram exactly; `Retired` proven terminal (no transition out of it) and a retired `id` proven never reusable.

## Synchronization, Event Integration, Telemetry (§11, §15, §16)

- [ ] `SyncPolicy` (§11) - `mode` (`"realtime"`/`"scheduled"`), `event_filter` (a plain `events.EventFilter`), optional `poll_interval`.
- [ ] `TwinSynchronizer.synchronize()` (§11) - fetches current `Twin` from `TwinRepository`, calls `_apply`, writes back the `with_state()`-produced replacement, returns `SyncResult`; confirmed to never mutate the `Twin` instance it reads.
- [ ] Live synchronization via `events.EventBus.subscribe(sync_policy.event_filter, handler)` implemented and tested (§15).
- [ ] Cold-start reconstruction via `events.EventStore.replay(as_of)` implemented and tested, proven to converge on the identical `TwinState` incremental synchronization would produce for the same event history (§15, §32's replay-consistency proof).
- [ ] `TelemetryReading` (§16) implemented as a plain value object; confirmed constructed only from already-event-sourced payload fields, never from a vendor SDK or wire protocol directly.

## State, Snapshot, Simulation Interface (§12, §13, §14)

- [ ] `TwinState` (§12) - `attributes: Mapping[str, Any]`, `captured_at`, `schema_version`; `validate()` rejects empty `attributes`.
- [ ] `TwinSnapshot` (§13) - `twin_id`, `state`, `status`, `as_of`; confirmed distinct from and never confused with `events.EventSnapshot` in code or tests.
- [ ] `TwinSimulationModel` (§14) - `_simulate(twin, hypothesis, as_of) -> TwinSimulationResult` signature only; zero concrete subclasses shipped.
- [ ] `TwinSimulationResult` (§14, §25) implemented even though no producer of it ships in this release.

## Twin Registry and Discovery (§17, §18)

- [ ] `digital_twin._registry.REGISTRY`/`register` (§17) - `Registry[str, type[Twin]]`, raising `TwinValidationError` for an empty code and `TwinVersionConflictError` for a materially-different re-registration under an existing code.
- [ ] `EntryPointSpec(group="mineproductivity.digital_twin", target_registry="digital_twin")` discovery wired via `registry.EntryPointDiscovery` (§28).
- [ ] `by_category()`/`by_scope()` (§18) - plain `core.PredicateSpecification` factories; composed with `TwinRepository.list()`; confirmed to return an empty sequence (never raise) for a filter matching nothing.

## Serialization and Persistence (§19, §20)

- [ ] Every `TwinState`/`TwinSnapshot`/`TwinResult` subclass and `Twin` itself confirmed to serialize via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer.
- [ ] `TwinRepository` implemented as `type TwinRepository = BaseRepository[Twin, str]` - a type alias, **not** a new ABC or subclass.
- [ ] Reference implementation uses `core.InMemoryRepository[Twin, str]()` directly, with zero new persistence code.
- [ ] Test suite for `TwinRepository` behavior written against the `core.BaseRepository[Twin, str]` contract alone, never against `InMemoryRepository`-specific internals (§32's repository-substitutability proof).

## Versioning (§21)

- [ ] `TwinMetadata.version` (type-level SemVer), `TwinStatus` (instance lifecycle), and `TwinState.schema_version` (data-shape version) confirmed to vary independently - no code path derives one from another.
- [ ] `TwinVersionConflictError` raised at registration time for a materially-different re-registration under an existing `TwinMetadata.code`, never deferred.

## Caching (§22)

- [ ] `TwinStateCache.get()`/`put()` (§22) implemented, keyed by `(twin_id, as_of)`.
- [ ] Confirmed **not** a reuse of `kpis.ResultCache` - cache key shape independently designed for twin-evidence bundles, not KPI-result semantics.
- [ ] Confirmed a cache miss (`get()` returning `None`) never raises and always falls back to direct re-assembly from `kpis.KPIEngine`/`analytics.BatchAnalyticsRunner`/`decision.BatchDecisionRunner`.
- [ ] Confirmed `TwinSynchronizer` never treats `TwinStateCache` as authoritative for "what is the twin's current state" - only `TwinRepository` is (§31's recorded anti-pattern).

## Validation

- [ ] `TwinMetadata.validate()` - non-empty `code`, category matches the closed `TwinCategory` namespace.
- [ ] `TwinState.validate()` - non-empty `attributes`.
- [ ] Each category base's namespace-convention check implemented (e.g. a `ConveyorTwin` asserting its `meta.code` falls in the conveyor namespace).
- [ ] `Twin._apply()` confirmed to never raise for a legitimately empty `events` batch - returns `self.state` unchanged instead.

## Error Handling

- [ ] Full exception hierarchy (design spec §6 `exceptions.py`): `TwinValidationError`, `TwinNotFoundError`, `TwinSyncError`, `TwinVersionConflictError`, `TwinStateConflictError` - each subclassing the matching `core` exception.
- [ ] `SyncResult.warnings` confirmed to be the primary "why didn't state change" signal; `TwinSyncError` reserved for genuinely exceptional conditions only, never for a legitimately-unchanged sync outcome.

## Result Models and Metadata (§25, §26)

- [ ] `TwinResult` base (`twin_id`, `computed_at`, `warnings`) and both concrete subclasses (`SyncResult`, `TwinSimulationResult`) implemented as frozen `core.BaseValueObject`s.
- [ ] Confirmed `TwinState`/`TwinSnapshot` are **not** `TwinResult` subclasses (they represent the twin itself, not an outcome of an orchestration call about it).
- [ ] `TwinCategory` enum (eleven members) and `TwinMetadata` (`code`, `category`, `description`, `version`) implemented; `validate()` rejects an empty `code`.

## Thread Safety & Concurrency

- [ ] `Twin` instances confirmed immutable and safe to share/read across threads with no locking.
- [ ] `TwinRepository`'s per-id write serialization contract documented and tested against any production-grade implementation candidate; confirmed the bare `core.InMemoryRepository` reference implementation provides **no** locking of its own (design spec §29) - any concurrent-write test against it must add external synchronization itself.
- [ ] `digital_twin.REGISTRY` confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract.
- [ ] Independent twins (different `id`s) proven to synchronize fully in parallel without contention; concurrent `synchronize()` calls for the *same* `twin_id` proven to serialize correctly (no lost update) once a conforming production `TwinRepository` is used.
- [ ] `TwinStateCache` reads/writes keyed by `(twin_id, as_of)` proven non-contending across independent keys.

## Tests

- [ ] `tests/unit/digital_twin/` mirrors `src/mineproductivity/digital_twin/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Unit tests per concrete twin category, each against a scripted event sequence with a known expected `TwinState` (§32).
- [ ] Identity/equality tests proving `BaseEntity`-inherited `__eq__`/`__hash__` behave correctly for `Twin` (§32).
- [ ] Synchronization correctness tests, cold-start reconstruction tests, and snapshot round-trip tests (§32).
- [ ] Registry/discovery isolation tests mirroring `tests/integration/test_registry_plugin_discovery.py`'s healthy/broken fixture-plugin pattern, specialized for `Twin` (§32).
- [ ] Interface-only ABC contract test for `TwinSimulationModel` (bare-ABC instantiation raises `TypeError`) - no algorithmic-correctness test exists for it (§32).
- [ ] Concurrency stress tests: same-`twin_id` serialization and different-`twin_id` non-interference (§32).
- [ ] The seven package acceptance proofs in design spec §32 (no-fact-recomputation, immutability, interface-purity, no-architectural-drift, replay-consistency, scope-immutability, repository-substitutability) each independently verified and recorded in the PR description.

## Documentation

- [ ] `digital_twin/README.md` complete.
- [ ] Every registered `Twin` type's docstring restates its `TwinMetadata.description` for source-level readability.

## Examples

- [ ] `examples/digital_twin/01_provision_and_sync.py` - the design spec §15 worked example (cold-start a `ConveyorTwin`, then live-subscribe), end-to-end.
- [ ] `examples/digital_twin/02_discovery.py` - `by_category`/`by_scope` composed lookups over a populated `TwinRepository`.
- [ ] `examples/digital_twin/03_snapshot_and_serialize.py` - `TwinSnapshot` capture, `core.serialization` round-trip.
- [ ] `examples/digital_twin/04_plugin_twin_type.py` - a third-party-style `Twin` type registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] `TwinRepository.get()`/`list()` latency at representative twin-population scale, recorded in `benchmark/reports/digital_twin/`.
- [ ] Cold-start replay cost vs. event history length, with and without `EventSnapshot` acceleration, recorded.

## Certification

- [ ] Design spec §32's seven package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility).

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked - confirm no forbidden import (`simulation`, `optimization`, `agents`, `visualization`) was introduced, and confirm no lower package gained a new `digital_twin` import.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §32's acceptance proofs re-verified as final merge gate.

---

*Derived from [`08_Digital_Twin_Design_Specification.md`](../architecture/08_Digital_Twin_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0008-Digital-Twin.md`](../adr/ADR-0008-Digital-Twin.md).*
