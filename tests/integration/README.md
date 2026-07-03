# Integration Tests

## Purpose

Tests that exercise interactions between two or more MineProductivity packages, validating the dependency contracts described in each package's README.

## Scope

Testing philosophy and conventions for `tests/integration/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Validate that layering rules are respected in practice (e.g., `kpis` correctly consuming `events`).
- May use real (but small, local) datasets from `tests/datasets/`.
- Slower than unit tests; run in CI on every PR but not necessarily on every local save.

## Contents

- `test_events_pipeline.py` — the full Event Framework pipeline: raw records → canonical events → contextual validation → envelope → durable append → bus publish → query/replay/snapshot → serialization round-trip. Plays the role of a minimal connector inline, since `connectors` does not exist yet.
- `test_ontology_model.py` — a multi-family mine model (location, equipment, organization, production, cost, safety) wired together with `Relationship` edges, validated end-to-end with `OntologyValidator`, projected through a `KnowledgeGraphProjection`, and cross-checked against `events.DelayEvent`/`events.SafetyEvent` to confirm the two packages share reference-data identity rather than duplicating it.
- `test_registry_plugin_discovery.py` — the Registry Framework's discovery and isolation guarantees proven against two real, independently pip-installed fixture plugin packages (`tests/fixtures/plugins/`), not mocks: one well-behaved, one that raises on import. Also exercises the full `PluginManifest` → `PluginLoader` → `PluginLifecycle` activation path against the same real fixtures.
- `conftest.py` — the session-scoped `registry_fixture_plugins_installed` fixture, which editable-installs the two registry test fixture packages before `test_registry_plugin_discovery.py` runs.
- `test_connector_pipeline.py` — the full CSV → `CSVConnector` → `EventValidator` → `EventStore` → query pipeline, plus Certification Categories A (golden fixture reproduction), C (edge cases), D (corrupted data, one malformed row isolated), and F (local-timezone normalization).

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
