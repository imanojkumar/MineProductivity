# Unit Tests

## Purpose

Fast, isolated tests for individual functions, classes, and modules within a single `src/mineproductivity` package.

## Scope

Testing philosophy and conventions for `tests/unit/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- One test sub-package per `src/mineproductivity` package, mirrored 1:1 by name.
- No network, filesystem, or cross-package integration — dependencies are faked or stubbed.
- Every public function/class added to a package must have corresponding unit tests in the same PR.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
