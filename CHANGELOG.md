# Changelog

All notable changes to MineProductivity are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note:** The software version (currently `0.2.0`) is independent of the
> architecture document version (`v1.0`, locked). The architecture is
> considered final for this phase; the software implementing it is not.

## [Unreleased]

### Added

- Nothing yet.

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
