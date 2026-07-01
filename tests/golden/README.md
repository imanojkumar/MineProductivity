# Golden Tests

## Purpose

Tests that compare implementation output against pre-approved, versioned 'golden' expected outputs (e.g., KPI computation results on canonical datasets).

## Scope

Testing philosophy and conventions for `tests/golden/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Golden outputs are versioned alongside the code that produces them.
- Changes to golden files require explicit review — they represent an intentional behavior change, not incidental drift.
- Golden datasets/outputs live in `tests/golden/` and reference `datasets/golden/` where applicable.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
