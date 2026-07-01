# Test Datasets

## Purpose

Small, purpose-built datasets scoped strictly to test usage — distinct from the top-level `datasets/` directory, which holds canonical/production-scale data.

## Scope

Testing philosophy and conventions for `tests/datasets/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Test datasets are minimal — just large enough to exercise the behavior under test.
- Never used as a substitute for the canonical datasets in top-level `datasets/canonical/`.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
