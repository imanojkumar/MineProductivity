# Changelog

All notable changes to MineProductivity are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note:** The software version (currently `0.3.0`) is independent of the
> architecture document version (`v1.0`, locked). The architecture is
> considered final for this phase; the software implementing it is not.

## [Unreleased]

### Added

- Nothing yet.

## [0.3.0] - 2026-07-03

### Added

- `mineproductivity.events`: the Event Framework — the immutable,
  append-only event model (Event Sourcing) every derived state in the
  platform is computed from, implementing
  `docs/architecture/01_Event_Framework_Design_Specification.md` exactly.
  `EventID` (ULID-backed, stdlib-only), `EventVersion`, `EventMetadata`,
  `EventEnvelope` (with the mandatory three-timestamp temporal model),
  `BaseEvent` and the six canonical event types (`CycleEvent`,
  `DelayEvent`, `MaintenanceEvent`, `ProductionEvent`, `ConsumptionEvent`,
  `SafetyEvent`), `EventSchema`, `EventValidator`/`ConfidenceScore`/
  `ValidationOutcome`, `EventStore`/`EventQuery`/`EventFilter` and a
  reference `_InMemoryEventStore`, `EventBus`/`Subscription` and a
  reference `_InMemoryEventBus`, `AsOf`/`ReplayHandle` (time-travel) and
  `EventSnapshot`, and three serialization codecs (`JSONEventCodec` with
  no extra dependency; `ArrowEventCodec`/`ParquetEventCodec` behind the
  new optional `events` extra).
- `mineproductivity.ontology.reference.DelayCategory`: the minimal shared
  contract (a closed six-value enum) published ahead of the full Ontology
  Framework milestone, per Documentation Governance Rule #005, because
  `events.DelayEvent` requires it. No other ontology concept exists yet.
- `tests/unit/events/`: a full unit test suite (229 tests, 100% line
  coverage), including dedicated property tests for idempotency and the
  replay/snapshot equivalence law.
- `tests/integration/test_events_pipeline.py`: the full ingest → validate
  → append → publish → query → replay → serialize pipeline, end to end.
- `examples/events/`: runnable examples for first-event construction,
  replay/time-travel, and corrections.
- `events/README.md`: architecture, dependency rules, public API
  reference, extension guide, design rationale, and anti-patterns.

### Fixed

- A `@dataclass(slots=True)` + inheritance + bare `super()` gotcha in
  `EventMetadata.validate()` (slotted dataclasses rebuild the class
  object, which breaks the implicit `__class__` cell a zero-arg `super()`
  relies on) — fixed with the explicit two-argument form, with a
  regression test guarding it.
- An Arrow/Parquet limitation where an all-empty `metadata.attributes`
  column across a batch produced a zero-child struct type that Parquet's
  writer cannot represent — fixed by JSON-string-encoding that one
  open-ended field for the Arrow/Parquet codecs specifically.

### Notes

- `events` depends on `core` and, minimally, `ontology.DelayCategory`
  only — mechanically verified (`tests/unit/events/test_public_api.py`)
  to import nothing from `connectors`, `kpis`, `analytics`,
  `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`.
- `pyproject.toml` gained an `events` optional-dependency group
  (`pyarrow`) and a `[[tool.mypy.overrides]]` entry for it (`pyarrow`
  ships no type stubs); the base install remains dependency-free.

## [0.2.0] - 2026-07-02

### Added

- `mineproductivity.core`: the platform's first implemented package,
  providing framework-agnostic, domain-agnostic foundational primitives —
  `BaseEntity`, `BaseValueObject`, `BaseIdentifier`/`UUIDIdentifier`,
  `BaseMetadata`, `BaseVersionedObject`, `BaseSpecification` (with
  `&`/`|`/`~` composition), `BaseRepository`/`InMemoryRepository`,
  `BaseFactory`, `BaseBuilder`, `BaseService`, `BaseValidator`/
  `ValidationResult`/`CompositeValidator`, `BaseSerializer`/
  `DataclassSerializer`, `BaseConfiguration`, `Result[T]`, `Maybe[T]`, the
  `MineProductivityError` exception hierarchy, and shared typing
  primitives (`Comparable`, `Identifiable`, `JSONValue`).
- `tests/unit/core/`: a full unit test suite for every `core` module
  (equality, hashing, immutability, validation, serialization, generics,
  ABC enforcement, edge cases).
- `examples/core/`: runnable examples demonstrating entities, value
  objects, repositories, factories, builders, validation, and
  serialization.
- `core/README.md`: architecture, dependency rules, public API reference,
  extension guide, design rationale, and anti-patterns for the package.

### Notes

- `core` has zero dependencies on any other `mineproductivity` package and
  zero knowledge of the mining domain (no KPI, event, ontology, equipment,
  dispatch, connector, analytics, optimization, digital twin, or decision
  concepts). Every other subsystem package remains an unimplemented
  structural placeholder.

## [0.1.0] - 2026-07-01

### Added

- Initial repository skeleton: full directory hierarchy for `src/`, `tests/`,
  `docs/`, `datasets/`, `notebooks/`, `examples/`, `benchmark/`,
  `certification/`, and `scripts/`, mirroring the locked Master Architecture
  Handbook v1.0 and Reference Implementation Blueprint v1.0.
- Packaging metadata (`pyproject.toml`) targeting Python 3.12+, using
  Hatchling and the `src/` layout.
- Governance and community files: `README.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md`, `CITATION.cff`.
- GitHub configuration: issue templates, pull request template, `CODEOWNERS`,
  and placeholder CI workflows (no CI logic implemented yet).
- Placeholder `README.md` files describing purpose, scope, responsibilities,
  contents, dependencies, future work, and references for every package and
  directory in the tree.

### Notes

- Zero business logic. No KPI calculations, digital twin implementation,
  connectors, AI agents, analytics, optimization, or event processing exist
  in this release.
