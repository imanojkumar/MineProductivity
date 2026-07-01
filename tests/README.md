# Tests

## Purpose

Root of the MineProductivity test suite, structured to mirror `src/mineproductivity/` and to enforce the project's test-first principle.

## Scope

Unit, integration, performance, regression, and golden tests, plus shared fixtures and test-only datasets. Does not include benchmark scenarios (see top-level `benchmark/`) or certification conformance tests (see top-level `certification/`), which are distinct, blueprint-level quality gates.

## Responsibilities

- Mirror the `src/mineproductivity/` package structure one-to-one under `tests/unit/`.
- House multi-package integration tests under `tests/integration/`.
- House performance and regression baselines.
- House golden/expected-output comparisons and shared fixtures/datasets.

## Contents

- `unit/` — one test package per `src/mineproductivity` package.
- `integration/` — cross-package and cross-layer tests.
- `performance/` — performance/benchmark-style tests (not to be confused with top-level `benchmark/`).
- `regression/` — regression tests guarding against previously fixed defects.
- `golden/` — golden-file/expected-output comparison tests.
- `fixtures/` — shared pytest fixtures and test doubles.
- `datasets/` — small, test-scoped datasets (distinct from top-level `datasets/`).

## Dependencies

`pytest`, `pytest-cov` (see `pyproject.toml` `[project.optional-dependencies].dev`).

## Future Work

Add tests alongside each package implementation, in the same pull request, per CONTRIBUTING.md.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
