# Shared Fixtures

## Purpose

Shared pytest fixtures, factories, and test doubles reused across unit, integration, performance, regression, and golden tests.

## Scope

Testing philosophy and conventions for `tests/fixtures/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Fixtures are domain-aware but implementation-free until packages exist to fix them against.
- Prefer fixture composition over duplication across test suites.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
