# Performance Tests

## Purpose

Tests that establish and guard performance baselines (throughput, latency, memory) for performance-sensitive subsystems (e.g., event processing, KPI computation at scale).

## Scope

Testing philosophy and conventions for `tests/performance/`. No implementation code lives here — only tests, fixtures, or test-scoped data as applicable.

## Responsibilities

- Track performance budgets, not correctness — correctness is covered elsewhere.
- Run on a defined cadence (not necessarily every PR) once implementation exists.
- Fail only on meaningful regression against a recorded baseline, not on noise.

## Contents

- Placeholder — populated as corresponding `src/mineproductivity` packages are implemented.

## Dependencies

`pytest` (see `pyproject.toml`).

## Future Work

Populate alongside implementation, per ROADMAP.md phasing and CONTRIBUTING.md's test-first rule.

## References

- Reference Implementation Blueprint v1.0
- Developer & Cookbook Guide — Part II
