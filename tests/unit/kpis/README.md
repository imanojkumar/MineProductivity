# Unit Tests — mineproductivity.kpis

## Purpose

Unit tests for `src/mineproductivity/kpis/`, mirroring its structure one-to-one.

## Scope

Isolated tests for `mineproductivity.kpis` only. Cross-package behavior (the full CSV → canonical events → `EventStore` → `KPIEngine` pipeline) belongs in `tests/integration/test_kpi_pipeline.py`.

## Responsibilities

- Cover every public symbol exported by `mineproductivity.kpis`.
- Guard the package's architectural rules mechanically (`test_public_api.py`): no forbidden cross-layer imports (`connectors` above all — the single most load-bearing rule in the design specification), no dependency beyond `core`/`ontology`/`events`/`registry`, `__all__` sorted with no gaps or duplicates, `engine.py` contains zero KPI-code-specific branches, every submodule importable in isolation with no circular imports.

## Contents

- `test_metadata.py`, `test_naming.py`, `test_lifecycle.py`, `test_base_kpi.py`, `test_composite.py`, `test_inheritance.py`, `test_result.py`, `test_engine.py`, `test_dependency_graph.py`, `test_aggregation.py`, `test_windowing.py`, `test_caching.py`, `test_validation.py`, `test_certification.py`, `test_exceptions.py`, `test_kpi_registry.py`, `test_public_api.py` — the cross-cutting root modules.
- `categories/` — namespace-conformance tests for all nine category base classes, parametrized rather than one near-duplicate file per category.
- `backends/` — one `test_*_backend.py` per `ExecutionBackend`, plus `test_backend_parity.py` (identical `KPIResult.value` across all four backends for every implemented KPI, and identical `group_and_aggregate` output — design spec §29).
- `standard_library/` — one `test_*.py` per flagship KPI, plus `test_standard_library_init.py` (the import-order-matters regression test for `@register`'s registration-time dependency-graph validation).
- `conftest.py` — shared `SHIFT_ID`/`make_shift`/`append_event`/`engine`/`event_store` fixtures used across the engine and standard-library tests.
- A dedicated regression test for the exact Cookbook Part I Ch. 6 ratio-correctness worked numbers (A-shift 1,300 t/h over 12h + B-shift 1,100 t/h over 6h combine to 1,233.3 t/h, never the naive 1,200 average), at both the row level (`test_engine.py::TestRatioNeverAveraged`) and the aggregation-refusal level (`test_aggregation.py`).
- A `ResultCache` concurrency stress test (32 threads racing the same cache key).
- **100% line coverage** of `src/mineproductivity/kpis/` (344 tests).

## Dependencies

`pytest`, `pytest-cov`, `mineproductivity[analytics]` (`pandas`, `numpy`, `polars`, `duckdb` — all four `ExecutionBackend`s are exercised for real, not mocked).

## Future Work

Add tests for each new public symbol in the same pull request that introduces it.

## References

- Reference Implementation Blueprint v1.0
- [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../../../docs/architecture/05_KPI_Engine_Design_Specification.md)
