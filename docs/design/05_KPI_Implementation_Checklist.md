# KPI Engine — Implementation Checklist

**Package:** `mineproductivity.kpis`
**Governing specification:** [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../architecture/05_KPI_Engine_Design_Specification.md)
**Status:** Not started

Binding implementation contract for `kpis` — the platform's most important package. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification read in full by the implementer, including the full cross-reference to Developer & Cookbook Guide Part III.
- [ ] `core`, `ontology`, `events` available and importable; `registry`, `validation`, `config` cross-cutting packages available.
- [ ] This checklist reviewed against the design spec's §36/§37 — no drift.
- [ ] Confirmed: `kpis` will not import `connectors` under any circumstance (design spec §7 — the single most load-bearing rule in this package).

## Package Structure

- [ ] `src/mineproductivity/kpis/` created matching design spec §6 exactly: `metadata.py`, `base_kpi.py`, `categories/` (nine files), `result.py`, `engine.py`, `dependency_graph.py`, `aggregation.py`, `windowing.py`, `composite.py`, `inheritance.py`, `caching.py`, `backends/` (five files), `naming.py`, `lifecycle.py`, `validation.py`, `certification.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `kpis/README.md` written following the `core/README.md` template.
- [ ] Confirmed `engine.py` contains zero KPI-code-specific branches (mechanical grep/AST check — design spec §37.1).

## Public API

- [ ] `kpis/__init__.py` exports exactly the symbol list in design spec §8, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py`.

## Interfaces / Object Model

- [ ] `KPIMetadata` (§10.1) — all 29 Standard Library fields represented (typed fields for engine-executed ones, `attributes` carrying documentation-only fields per design spec §34), plus naming/lifecycle/applicability fields.
- [ ] `Direction`, `Aggregation`, `DigitalMaturity`, `KPIStatus` enums (§10.2) — exact members per spec.
- [ ] `BaseKPI` (§10.3) — `compute()` non-overridable orchestration, `_compute()` abstract, `_required_columns()` derived from metadata.
- [ ] Nine category base classes (§10.4): `ProductionKPI`, `UtilizationKPI`, `MaintenanceKPI`, `HaulageKPI`, `DelayKPI`, `EnergyKPI`, `QualityKPI`, `CostKPI`, `SafetyKPI` — each with a namespace-prefix validation check.
- [ ] `TonnesPerHour` reference exemplar (§10.5) implemented exactly, including its full `KPIMetadata`.
- [ ] `KPIResult` (§10.6) — `to_frame()`, `plot()`, `pareto()` delegate to backend/visualization-metadata hooks.
- [ ] `CompositeKPI` (§10.7) — `_combine()` abstract; `_compute()` raises `NotImplementedError` by design.
- [ ] `specialize()` inheritance helper (§10.7) — proves `PROD.TPH.Ore`/`PROD.TPH.Waste`-style specialization.
- [ ] `KPIEngine` (§10.8) — `execute()`, `rows_for()`; confirmed to hold no metric-specific logic.
- [ ] `DependencyGraph` (§10.8) — `topological_order()`, `detect_cycle()` (non-raising).
- [ ] `ExecutionBackend` ABC + `PolarsBackend`, `DuckDBBackend`, `PandasBackend`, `NumPyBackend` (§10.9).
- [ ] `Window`, `RollingWindow`, `CumulativeWindow` (§10.10).

## Lifecycle & State Machine

- [ ] KPI type lifecycle (§11): Proposed → Active → Deprecated → Retired, aliases resolving indefinitely from `Deprecated`.
- [ ] `KPIEngine.execute()` internal state machine (§12): Requested → Resolving → (Failed | Assembling) → ComputingDependencies → ComputingTarget → (Cached | Computed).
- [ ] Retired KPI codes proven never reusable (registration-time check against historical retirement record).

## Validation

- [ ] `KPIMetadata.validate()` — identifier parses as `NAMESPACE.Name` (§20), all mandatory fields populated.
- [ ] `BaseKPI.compute()` — missing-column detection produces a warning-carrying `KPIResult`, never an exception.
- [ ] Canonical time-model invariant enforced for every `UtilizationKPI`: `calendar ⊇ scheduled ⊇ available ⊇ operating`; `UTIL.EU == UTIL.PA × UTIL.UA` proven by test.
- [ ] Six-category delay taxonomy consumed correctly by every `DelayKPI` (cross-package test against `ontology.DelayCategory`).
- [ ] RATIO-never-averaged rule enforced structurally by the engine, not by convention (design spec §19, §29) — dedicated regression test using the exact Cookbook Part I Ch. 6 worked numbers.

## Versioning

- [ ] `parse_identifier()` (§20) validates `NAMESPACE.Name` against the full controlled namespace list (`PROD`, `UTIL`, `MAINT`, `HAUL`, `DISP`, `QUAL`, `COST`, `ENERGY`, `CARBON`, `WATER`, `SAFE`, `AUTO`, `GRADE`, `BLEND`, `CRUSH`, `PROC`, `STOCK`, `RAIL`, `PORT`, `TWIN`, `DI`, `AI`).
- [ ] `KPIVersionConflictError` raised when a plugin attempts to re-register an existing Active code with materially different metadata without a MAJOR bump.
- [ ] Aliases/deprecated-successor resolution tested.

## Serialization

- [ ] `KPIMetadata`/`KPIResult` serialize via `core.serialization` for documentation/API export.
- [ ] `KPIResult.to_frame()` delegates correctly to the active `ExecutionBackend`.

## Performance & Memory

- [ ] Column pruning proven: requesting `PROD.TPH` does not load delay/quality columns (test asserts the assembled query's column set).
- [ ] Batched multi-KPI request path (`mine.summary`-equivalent) proven to scan the event store once, not once per KPI.
- [ ] `ResultCache` write-through and cache-key correctness (`(code, window, scope, event-store-version-fingerprint)`) tested, including invalidation on new relevant events.

## Thread Safety & Concurrency

- [ ] `BaseKPI` subclasses confirmed stateless across `compute()` calls (no instance mutation).
- [ ] `ResultCache` writes proven safe under concurrent `execute()` calls for the same cache key (stress test).
- [ ] Independent concurrent KPI executions (different code/window/scope) proven non-interfering.

## Error Handling

- [ ] Full exception hierarchy (§26): `KPIValidationError`, `KPINotFoundError`, `KPICircularDependencyError`, `KPIAggregationError`, `KPIVersionConflictError`.
- [ ] `KPICircularDependencyError` proven to raise at *registration* time, never deferred to first execution.
- [ ] Confirmed a `None`-valued upstream dependency propagates as `None` with a warning through a composite KPI, never crashes and never becomes a fabricated zero.

## Logging

- [ ] Every non-empty-`warnings` `KPIResult` logged at `WARNING` with code, scope, warning text.
- [ ] Registry rejections (`KPIVersionConflictError`, duplicates) logged at `WARNING`.
- [ ] `DependencyGraph` cycle detection failures logged at `ERROR` at registration time.

## Configuration

- [ ] `KPIEngineConfiguration.backend` (default `"pandas"`) implemented as `core.BaseConfiguration`.
- [ ] `ResultCacheConfiguration` (size/TTL bounds) implemented.
- [ ] Site-level time-model conventions (e.g. whether queueing counts as operating time) confirmed sourced externally, never hard-coded in any `UtilizationKPI`.

## Tests

- [ ] `tests/unit/kpis/` mirrors `src/mineproductivity/kpis/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Per-KPI unit tests against Standard Library worked examples (at minimum: `TonnesPerHour` plus one flagship per remaining category).
- [ ] Aggregation property tests (RATIO-never-averaged) for every RATIO-aggregation KPI implemented.
- [ ] `DependencyGraph` topological-order and cycle-detection tests.
- [ ] Backend parity tests: identical `KPIResult.value` across all four `ExecutionBackend`s for every implemented KPI, within documented floating-point tolerance.

## Documentation

- [ ] `kpis/README.md` complete.
- [ ] Every registered KPI's docstring restates its `KPIMetadata.business_purpose`/`operational_question` for source-level readability.

## Examples

- [ ] `examples/kpis/01_simple_execution.py` — `PROD.TPH` end-to-end (design spec §31).
- [ ] `examples/kpis/02_composite_oee.py` — `UTIL.OEE` composite execution.
- [ ] `examples/kpis/03_batch_summary.py` — multi-KPI single-scan execution.
- [ ] `examples/kpis/04_discovery.py` — `REGISTRY` introspection, `describe()`.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] Single-KPI vs. batch-summary scan-count comparison recorded in `benchmark/reports/kpis/`.
- [ ] Backend performance comparison (Polars/DuckDB/pandas/NumPy) recorded at representative fleet-scale row counts.
- [ ] Cache hit/miss latency recorded.

## Certification

- [ ] Categories A (golden), B (integration), C (edge cases), D (corrupted data), E (missing data), G (multi-mine), H (multi-commodity) from design spec §30 pass.
- [ ] Design spec §37's six acceptance-criteria proofs (KPI-as-object, ratio-correctness, composite-correctness, backend parity, no architectural drift, cross-reference audit) each independently verified and recorded in the PR description.

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked — confirm no forbidden import (`connectors`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, `agents`) was introduced.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §37 re-verified as final merge gate.

---

*Derived from [`05_KPI_Engine_Design_Specification.md`](../architecture/05_KPI_Engine_Design_Specification.md). Keep in sync with the governing specification.*
