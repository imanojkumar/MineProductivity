# Event Framework — Implementation Checklist

**Package:** `mineproductivity.events`
**Governing specification:** [`docs/architecture/01_Event_Framework_Design_Specification.md`](../architecture/01_Event_Framework_Design_Specification.md)
**Status:** Not started

This checklist is the binding implementation contract for `events`. A pull request may not be merged into the package until every applicable box is checked (or explicitly deferred with a linked follow-up issue and Chief Software Architect sign-off). Check items off in order — later sections assume earlier ones are done.

## Pre-Implementation Gate

- [ ] Design specification read in full by the implementer.
- [ ] `core` (v0.2.0) and `ontology` (once implemented) are available and importable.
- [ ] This checklist reviewed against the design spec's §36 (Definition of Done) and §37 (Package Acceptance Criteria) — no drift between the two documents.

## Package Structure

- [ ] `src/mineproductivity/events/` created matching design spec §6 exactly: `envelope.py`, `identifier.py`, `versioning.py`, `base_event.py`, `schema.py`, `canonical/`, `validation.py`, `store.py`, `bus.py`, `replay.py`, `snapshot.py`, `serialization/`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `events/README.md` written following the `core/README.md` template (Purpose, Architecture, Dependency rules, Public API, Extension guide, Examples, Design rationale, Anti-patterns, Future packages).
- [ ] No module outside `canonical/` contains a concrete `BaseEvent` subclass.

## Public API

- [ ] `events/__init__.py` exports exactly the symbol list in design spec §8, alphabetized in `__all__`, mirroring `core/__init__.py`'s convention.
- [ ] Every exported symbol is reachable via `from mineproductivity.events import X` with no internal-module import required.
- [ ] A `test_public_api.py` (mirroring `tests/unit/core/test_public_api.py`) asserts `__all__` completeness, sortedness, and no duplicate entries.

## Interfaces / Object Model

- [ ] `EventID` (§10.1) — ULID-backed `BaseIdentifier[str]`, `generate()` classmethod.
- [ ] `EventVersion` (§10.2) — `BaseVersionedObject`, monotonic, never resets.
- [ ] `EventMetadata` (§10.3) — `BaseMetadata` subclass with `confidence`, `source_system`, `late_arrival`.
- [ ] `EventEnvelope` (§10.4) — three-timestamp invariant enforced in `validate()`.
- [ ] `BaseEvent` (§10.5) — abstract, `equipment_id`/`shift_id`/`event_type_code` contract.
- [ ] All six canonical event types (§10.6): `CycleEvent`, `DelayEvent`, `MaintenanceEvent`, `ProductionEvent`, `ConsumptionEvent`, `SafetyEvent` — full field lists per spec table, each with `validate()` and `duration_h()`.
- [ ] `EventSchema` (§10.7) — `to_json_schema()` implemented.
- [ ] `EventStore` ABC (§10.8) — `append`, `append_batch`, `get`, `find`, `query`, `replay`, `snapshot`.
- [ ] `EventQuery` (§10.8) — reuses `core.BaseSpecification` for `filters`.
- [ ] `EventBus` ABC and `Subscription` (§10.9).
- [ ] Reference `_InMemoryEventStore` and `_InMemoryEventBus` implemented for tests/examples (not exported publicly).

## Lifecycle & State Machine

- [ ] Envelope lifecycle (§11) implemented exactly: Produced → Validated → (Rejected | ConfidenceScored) → Enveloped → Appended → Published.
- [ ] `EventVersion` correction state machine (§12) — `Retracted` implemented via metadata flag, never a delete.
- [ ] Idempotency proven: re-appending the same `(EventID, EventVersion)` is a no-op (unit test required).

## Validation

- [ ] Structural validation (`BaseEvent.validate()`) — every canonical type's field invariants (§19.1, per-type table).
- [ ] Contextual validation (`EventValidator`, §19.1) — orphaned ontology reference produces a confidence penalty, never a silent drop.
- [ ] `ConfidenceScore` (§19.2) — bounds-checked `[0.0, 1.0]`.
- [ ] The six `DelayCategory` values and precedence order (§19.3) enforced — cross-check against Ontology package once available.

## Versioning

- [ ] `EventVersion` correction counter behavior tested (append v1, append v2, `EventQuery(as_of_version_policy="latest")` returns v2; `as_of_version` pins v1).
- [ ] `EventSchema.version` SemVer discipline documented in `README.md` and enforced by a lint/review checklist item (no code-level enforcement expected at v1.0).

## Serialization

- [ ] `JSONEventCodec` — round-trips via `core.to_dict`/`DataclassSerializer` conventions.
- [ ] `ArrowEventCodec` — one `RecordBatch` per event type; columns match `EventSchema.field_types`.
- [ ] `ParquetEventCodec` — partitioned by `(site, event_type_code, date(event_time_utc))`.
- [ ] All three codecs implement `core.BaseSerializer[EventEnvelope]` uniformly (parity test: same envelope round-trips identically through all three, modulo format-specific precision).

## Performance & Memory

- [ ] Every connector-facing and query-facing API returns an `Iterator`/generator — verified by a test asserting no full materialization for a large synthetic fixture.
- [ ] Column-pruned query path exercised against the Arrow/Parquet codecs.
- [ ] Snapshot equivalence law (design spec §17.1) proven by property test: `replay(as_of) == fold(query(since=snapshot.as_of, until=as_of), initial=snapshot.state)`.

## Thread Safety & Concurrency

- [ ] `_InMemoryEventStore.append()` safe under concurrent calls for different `EventID`s (stress test with a thread pool).
- [ ] Idempotent behavior confirmed under concurrent re-append of the same `(EventID, EventVersion)`.
- [ ] `EventBus.publish()` confirmed to fire only after durable `append()` completion (sequence test).

## Error Handling

- [ ] Full exception hierarchy implemented (§26): `EventValidationError`, `EventVersionConflictError`, `DuplicateEventError`, `EventNotFoundError`, `ReplayError`, all rooted in `core.MineProductivityError` via `ValidationError`/`NotFoundError`.
- [ ] Every rejection path returns `Result.err`, never raises past a public API boundary except where explicitly documented (`get()` raising `EventNotFoundError` is the one raising exception per spec — confirm `find()` is the non-raising counterpart).

## Logging

- [ ] Append rejections logged at `WARNING` with `EventID` + attempted `EventVersion` + reason.
- [ ] Late-arrival acceptances logged at `INFO` with lateness duration.

## Configuration

- [ ] `LateEventPolicy` (§28) implemented as a `core.BaseConfiguration` subclass with the three documented modes.

## Tests

- [ ] `tests/unit/events/` mirrors `src/mineproductivity/events/` 1:1.
- [ ] Coverage ≥95% (matching `core`'s bar).
- [ ] Property tests: idempotency, replay/snapshot equivalence.
- [ ] Contract test suite for `EventStore`/`EventBus` implementations exists and `_InMemoryEventStore`/`_InMemoryEventBus` pass it.
- [ ] Golden tests: fixed envelope sequence replayed to a fixed `as_of` reproduces a pinned expected state.

## Documentation

- [ ] `events/README.md` complete (see Package Structure above).
- [ ] Every public class/function has a docstring in the `core`-established style (summary + Parameters/Raises/Examples where relevant).

## Examples

- [ ] `examples/events/01_first_event.py` — construct, validate, append, query (mirrors design spec §31).
- [ ] `examples/events/02_replay.py` — demonstrates `replay(as_of)` time travel.
- [ ] `examples/events/03_correction.py` — demonstrates a version-2 correction and `as_of_version`.
- [ ] All examples run cleanly end-to-end and are checked by `mypy --strict` + `ruff`.

## Benchmarks

- [ ] A synthetic large-fixture benchmark (order of Cookbook's "50-million-row shift export" claim, scaled appropriately for CI) confirms streaming behavior holds under load.
- [ ] Snapshot-vs-full-replay cost comparison recorded in `benchmark/reports/events/`.

## Certification

- [ ] Categories A (golden), B (integration), C (edge cases), D (corrupted data), E (missing data), F (timezone), G (multi-mine) from design spec §30 all pass against `_InMemoryEventStore`.
- [ ] Certification fixtures sourced from `datasets/golden/` and `datasets/canonical/`.

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached to the PR; ≥95% line coverage.

## Release

- [ ] `CHANGELOG.md` updated with the `events` package's addition.
- [ ] Root README's dependency diagram cross-checked — no drift from design spec §7.
- [ ] Package version bump proposed and reviewed (do not self-merge a version bump).
- [ ] Design spec §37 (Package Acceptance Criteria) re-verified as a final gate before merge.

---

*Derived from [`01_Event_Framework_Design_Specification.md`](../architecture/01_Event_Framework_Design_Specification.md). Update this checklist if the governing specification changes; do not let them drift silently.*
