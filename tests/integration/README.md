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

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
