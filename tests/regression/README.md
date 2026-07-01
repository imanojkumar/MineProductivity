# Regression Tests

## Purpose

Tests that pin down previously identified and fixed defects so they cannot silently reoccur.

## Scope

Testing philosophy and conventions for `tests/regression/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Every non-trivial bug fix ships with a regression test reproducing the original failure.
- Regression tests reference the issue/PR that introduced them in a code comment.
- Never deleted without explicit justification, even after refactors.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
