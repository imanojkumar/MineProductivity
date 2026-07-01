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

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
