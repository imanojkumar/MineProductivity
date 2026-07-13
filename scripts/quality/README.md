# Scripts - quality

## Purpose

Linting, type-checking, and other quality-gate scripts run locally or in CI.

## Scope

Operational scripts only. No application/package code.

## Responsibilities

- House quality tooling scripts.

## Contents

- `smoke_test.py` - post-install smoke test: imports every implemented subpackage and runs one real KPI computation. Dependency-light by design (base install only, no extras); used by `.github/workflows/ci.yml`'s install-validation jobs (editable/wheel/sdist/GitHub installs) and runnable standalone after any local install.
- `check_docs.py` - documentation validation: every relative link across every Markdown file in the repository resolves, and every fenced ```python block in the root README and each implemented package's README executes without error. Used by `.github/workflows/quality.yml`.
- `perf_smoke.py` - performance smoke test, not a benchmark: generous wall-clock ceilings on cold-import time, a batched KPI compute, and dependency-graph resolution, meant to catch a catastrophic regression (an accidental O(n²), a broken cache), not track performance over time. Does not depend on the unimplemented `mineproductivity.benchmark` package. Used by `.github/workflows/benchmark.yml`.

## Dependencies

`mineproductivity` itself (editable-installed); no third-party packages beyond what `mineproductivity[dev]` already provides.

## Future Work

Add quality scripts as operational needs arise.

## References

- CONTRIBUTING.md
