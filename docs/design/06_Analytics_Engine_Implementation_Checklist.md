# Analytics Engine - Implementation Checklist

**Package:** `mineproductivity.analytics`
**Governing specification:** [`docs/architecture/06_Analytics_Engine_Design_Specification.md`](../architecture/06_Analytics_Engine_Design_Specification.md)
**Architecture Decision Record:** [`docs/adr/ADR-0006-Analytics-Engine.md`](../adr/ADR-0006-Analytics-Engine.md)
**Status:** Not started

Binding, **locked** implementation contract for `analytics` - the first package built on top of the now-locked Foundation Layer (`core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis`). Nothing described here may be implemented before this checklist and its governing specification exist in reviewed form, and nothing may be implemented that is not represented by an item on this list - an implementer who finds a gap corrects the governing specification and this checklist first, in a separate documentation PR, before writing the code the gap would have covered. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification (`06_Analytics_Engine_Design_Specification.md`) read in full by the implementer, including every cross-reference to specs 01–05.
- [ ] ADR-0006 read in full; the rationale for `analytics` existing as a separate package (not folded into `kpis`, not deferred until `decision` needs it) is understood, not merely accepted.
- [ ] `core`, `events`, `ontology`, `registry`, `plugins`, `connectors`, `kpis` available and importable, exactly as released (v0.2.0–v0.7.0); no Foundation Layer file is modified as a side effect of this work (design spec Document Control).
- [ ] Confirmed: `analytics` will not import `decision`, `digital_twin`, `optimization`, `simulation`, `agents`, or `visualization` under any circumstance - none of those packages exist yet (design spec §5).
- [ ] Confirmed: no Foundation Layer file (`core` through `kpis`) will be modified to import or otherwise reference `analytics` (design spec §5, §3.5).

## Package Structure

- [ ] `src/mineproductivity/analytics/` created matching design spec §6 exactly: `abstractions.py`, `metadata.py`, `result.py`, `pipeline.py`, `aggregation.py`, `windowing.py`, `timeseries.py`, `statistics.py`, `rolling.py`, `trend.py`, `baseline.py`, `benchmarking.py`, `quality.py`, `forecasting.py`, `anomaly.py`, `outliers.py`, `batch.py`, `streaming.py`, `incremental.py`, `_registry.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `analytics/README.md` written following the `core/README.md` template (per every prior package's own precedent).
- [ ] Confirmed `pipeline.py` contains zero model-specific branches (mechanical grep/AST check - design spec §9, mirroring spec 05 §37.1's `KPIEngine` proof).
- [ ] Confirmed `forecasting.py`, `anomaly.py`, `outliers.py` contain zero concrete, non-test subclasses of `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` (design spec §16, §18, §19, §35's interface-purity proof).

## Public API

- [ ] `analytics/__init__.py` exports exactly the symbol list in design spec §7, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py` and every existing package's own copy of it.
- [ ] `TestNoForbiddenDependencies` AST-walks every `analytics` submodule for a forbidden import (`decision`, `digital_twin`, `optimization`, `simulation`, `agents`, `visualization`) - mirrors every existing package's own copy of this test (design spec §5).
- [ ] A second, reverse-direction test asserts no file under `src/mineproductivity/{core,ontology,events,registry,plugins,connectors,kpis}/` imports `mineproductivity.analytics` (design spec §5, §3.5) - this is new relative to prior packages' checklists, since `analytics` is the first package for which "nothing below imports up" needs its own explicit proof.

## Abstractions & Registry (§8, §32, §33)

- [ ] `AnalyticsModel` (§8) - `analyze()` non-overridable orchestration enforcing `meta.min_observations`; `_analyze()` abstract.
- [ ] `AnalyticsContext` (§8) - bundles `EventStore`, optional `KPIEngine`, optional `ExecutionBackend`.
- [ ] `AnalyticsMetadata`/`AnalyticsCategory` (§31) - `code`, `category`, `description`, `min_observations`, `version`; `validate()` rejects an empty `code`.
- [ ] `analytics._registry.REGISTRY`/`register` (§33) - `Registry[str, type[AnalyticsModel]]`, raising `AnalyticsValidationError` for an empty code and `AnalyticsVersionConflictError` for a materially-different re-registration under an existing code.
- [ ] `EntryPointSpec(group="mineproductivity.analytics", target_registry="analytics")` discovery wired via `registry.EntryPointDiscovery` (§33).

## Metric Pipelines & Aggregation (§9, §10)

- [ ] `PipelineStage` (ABC) and `AnalyticsPipeline` (§9) - `run()` chains stages in order, rejects a pipeline whose final stage does not yield an `AnalyticsResult`.
- [ ] `ModelStage` (§9) - the concrete terminal stage wrapping one `AnalyticsModel`.
- [ ] `AggregationEngine.reduce()` (§10) - pure statistical group-and-reduce over non-KPI series (`sum`/`mean`/`median`).
- [ ] `AggregationEngine.reduce_kpi_results()` (§10) - for `ADDITIVE`/`CUMULATIVE`-aggregation KPIs, direct combination; for `RATIO`/`AVERAGE`/`WEIGHTED_AVERAGE`-aggregation KPIs, delegates to `KPIEngine.execute()` over the combined scope - **never** averages already-computed `KPIResult.value`s for these aggregation kinds (design spec §10, §34 - the single most load-bearing correctness rule in this package, direct analogue of `kpis`' own ratio-never-averaged rule, spec 05 §19, §13.3).

## Windowing & Time-Series (§11, §12)

- [ ] `RollingSpec` (§11) - exactly one of `time_window` (wrapping `kpis.RollingWindow`) or `periods` (count-based) set; `validate()` enforces this.
- [ ] `TimeSeries`/`TimeSeriesPoint` (§12) - ordered by timestamp; `from_kpi_results()` and `from_event_query()` construction paths implemented.
- [ ] Confirmed no second, parallel time-window type is introduced anywhere in the package (design spec §34).

## Trend, Baseline, Benchmarking (§13, §14, §15)

- [ ] `TrendModel` (ABC) / `LinearTrendModel` (§14) - deterministic OLS fit; `TrendResult` carries `slope`, `intercept`, `r_squared`, `direction`.
- [ ] `BaselineModel` (ABC) / `RollingBaselineModel` (§15) - trailing mean/std band; `Baseline` result carries `mean`, `std`, `lower`, `upper`.
- [ ] `BenchmarkModel` (ABC) / `BandBenchmarkModel` (§13) - reads `KPIMetadata.benchmark_bands`/`direction` via `Registry.metadata_for`; correctly inverts comparison for `LOWER_IS_BETTER`, handles `TARGET_IS_BEST` as distance-from-target.
- [ ] Confirmed `BandBenchmarkModel` introduces no parallel band schema - every band classification traces to an existing `KPIMetadata.benchmark_bands` entry (design spec §13, §34).

## Interface-Only Modules (§16, §18, §19)

- [ ] `ForecastingModel` (ABC) - `_forecast(series, horizon, context) -> ForecastResult` signature only; zero concrete subclasses shipped.
- [ ] `AnomalyDetector` (ABC) - `_detect(series, baseline, context) -> Sequence[AnomalyFlag]` signature only; zero concrete subclasses shipped.
- [ ] `OutlierDetector` (ABC) - `_detect(series, distribution, context) -> Sequence[OutlierFlag]` signature only; zero concrete subclasses shipped.
- [ ] `ForecastResult`, `AnomalyFlag`, `OutlierFlag` result types implemented per §16/§18/§19 even though no producer of them ships in this release.

## Statistical Primitives (§17, §20–§24)

- [ ] `describe()` → `StatisticalSummary` (§17).
- [ ] `percentile()` (§21) - linear-interpolation convention, matching NumPy's/pandas' default.
- [ ] `histogram()` → `Histogram` (§22) - supports both integer bin count and caller-supplied bin edges.
- [ ] `distribution()` → `DistributionSummary` (§23) - adds `skewness`/`kurtosis` beyond `describe()`.
- [ ] `confidence_interval()` → `ConfidenceInterval` (§24) - `normal` and `t` methods only; no resampling-based method in this release (§37).
- [ ] `rolling_mean()`, `rolling_std()`, `rolling_apply()` (§20) - absent-point (not sentinel-value) representation before `spec.min_periods` observations are available.

## Data Quality & Missing Data (§25, §26)

- [ ] `DataQualityScorer.score()` → `DataQualityScore` (§25) - `completeness`, `validity`, `overall_score`, `reasons`.
- [ ] `DataQualityStage` (§6, §9) - the `PipelineStage` wrapper composing `DataQualityScorer` into an `AnalyticsPipeline`.
- [ ] `MissingDataPolicy` enum (§26) - exactly `EXCLUDE`, `FLAG_ONLY`, `FORWARD_FILL`, `MEAN_FILL`; no fifth, predictive/model-based member.

## Execution Modes (§27, §28, §29)

- [ ] `BatchAnalyticsRunner` (§28) - thin, named wrapper over `AnalyticsPipeline.run()`.
- [ ] `StreamingAnalyticsSession` (§27) - `start()` returns the `events.Subscription` handle from `EventBus.subscribe()`; `snapshot()` reads without touching `EventStore`.
- [ ] `IncrementalAccumulator` (§29) - Welford's online algorithm; `update()`/`snapshot()`; per-key synchronization documented and implemented in `StreamingAnalyticsSession` (§29's thread-safety contract - `IncrementalAccumulator` itself is not internally synchronized).
- [ ] Streaming/batch parity proven: `IncrementalAccumulator`'s result and `statistics.describe()`'s batch result agree within floating-point tolerance over the same dataset (§35, §36).

## Result Models & Serialization (§30)

- [ ] `AnalyticsResult` base (`model_code`, `computed_at`, `warnings`) and every concrete subclass (`StatisticalSummary`, `TrendResult`, `BenchmarkResult`, `Baseline`, `DistributionSummary`, `Histogram`, `ConfidenceInterval`, `DataQualityScore`, `ForecastResult`) implemented as frozen `core.BaseValueObject`s.
- [ ] `AnomalyFlag`/`OutlierFlag` implemented as plain `BaseValueObject`s (not `AnalyticsResult` subclasses) per §30's explicit distinction.
- [ ] Every result type serializes via `core.serialization` (`DataclassSerializer`/`to_dict`) with no bespoke per-type serializer (§30).

## Thread Safety & Concurrency

- [ ] Every `AnalyticsModel` subclass confirmed stateless across `analyze()` calls (no instance mutation) - test proves concurrent invocation of one shared instance is safe (§8).
- [ ] `analytics.REGISTRY` confirmed read-only and thread-safe after startup discovery, inheriting `Registry`'s own contract (§8, spec 03 §24).
- [ ] `IncrementalAccumulator` confirmed **not** thread-safe on its own; `StreamingAnalyticsSession`'s per-key serialization mechanism (lock or equivalent) implemented and stress-tested under concurrent `update()` calls for the same key (§29).
- [ ] Independent `IncrementalAccumulator`s (different keys) proven non-interfering under concurrent updates (§29).

## Error Handling

- [ ] Full exception hierarchy (design spec §6 `exceptions.py`, used throughout §8–§33): `AnalyticsValidationError`, `InsufficientDataError`, `AnalyticsModelNotFoundError`, `AnalyticsVersionConflictError` - each subclassing the matching `core` exception (`ValidationError`, `ValidationError`, `NotFoundError`, `RegistrationError` respectively).
- [ ] Confirmed `AnalyticsModel.analyze()` never raises for a legitimately un-analyzable input (too few observations) - returns a warning-carrying `AnalyticsResult` instead (§8, §34).
- [ ] `AnalyticsVersionConflictError` proven to raise at *registration* time for a materially-different re-registration under an existing code, never deferred (§33).

## Performance & Memory

- [ ] `IncrementalAccumulator` confirmed as the default posture for unbounded input in both `StreamingAnalyticsSession` and, where row counts are large, `BatchAnalyticsRunner` (§36).
- [ ] `AggregationEngine` confirmed to accept and correctly delegate to an optional `kpis.ExecutionBackend`, with a plain-Python fallback when none is supplied - no second vectorization abstraction introduced (§36).
- [ ] `TimeSeries.from_event_query()` confirmed to request only `value_field` plus scope/grouping fields, never a full envelope payload, when constructing a series for pure statistical description (§36).

## Tests

- [ ] `tests/unit/analytics/` mirrors `src/mineproductivity/analytics/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Unit tests per concrete model (`LinearTrendModel`, `RollingBaselineModel`, `BandBenchmarkModel`) against hand-computed reference values (§35).
- [ ] Statistical primitive tests (`percentile`, `histogram`, `distribution`, `confidence_interval`) against independently-verified reference values, not self-referential re-assertions (§35).
- [ ] `AggregationEngine.reduce_kpi_results` regression test reproducing spec 05 §13.3's exact worked example at the cross-group level (§10, §35).
- [ ] Registry/discovery isolation tests mirroring `tests/integration/test_registry_plugin_discovery.py`'s healthy/broken fixture-plugin pattern, specialized for `AnalyticsModel` (§35).
- [ ] Interface-only ABC contract tests for `ForecastingModel`/`AnomalyDetector`/`OutlierDetector` (bare-ABC instantiation raises `TypeError`; minimal test-only concrete subclass satisfies the signature) - no algorithmic-correctness test exists for any of the three (§35).
- [ ] Streaming/incremental parity test (§29, §35).
- [ ] Data-quality scoring tests against rows with known, hand-counted missing/invalid fields (§35).
- [ ] The five package acceptance proofs in design spec §35 (no-KPI-recomputation, ratio-correctness-at-the-group-level, interface-purity, no-architectural-drift, streaming/batch parity) each independently verified and recorded in the PR description.

## Documentation

- [ ] `analytics/README.md` complete.
- [ ] Every registered `AnalyticsModel`'s docstring restates its `AnalyticsMetadata.description` for source-level readability (mirrors `kpis`' equivalent convention, spec 05 checklist).

## Examples

- [ ] `examples/analytics/01_pipeline_over_kpi_series.py` - the design spec §9 worked example (90-day `PROD.TPH` trend, gated by `DataQualityStage`), end-to-end.
- [ ] `examples/analytics/02_benchmarking.py` - `BandBenchmarkModel` classifying a `KPIResult` against its `KPIMetadata.benchmark_bands`.
- [ ] `examples/analytics/03_streaming_session.py` - `StreamingAnalyticsSession` over an `EventBus`, snapshotting a live `StatisticalSummary`.
- [ ] `examples/analytics/04_plugin_model.py` - a third-party-style `AnalyticsModel` registered via entry points, mirroring `examples/registry/01_register_and_discover.py`'s pattern.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] `IncrementalAccumulator` vs. full batch `statistics.describe()` recompute - latency comparison at representative event-volume scale, recorded in `benchmark/reports/analytics/`.
- [ ] `AggregationEngine` with vs. without an `ExecutionBackend` supplied - throughput comparison at representative row counts.

## Certification

- [ ] Design spec §35's five package acceptance proofs pass and are recorded in the PR description (duplicated here from Tests for merge-gate visibility, mirroring spec 05 checklist's own Certification section referencing its design spec's §37).

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked - confirm no forbidden import (`decision`, `digital_twin`, `optimization`, `simulation`, `agents`, `visualization`) was introduced, and confirm no Foundation Layer file gained a new `analytics` import.
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §35's acceptance proofs re-verified as final merge gate.

---

*Derived from [`06_Analytics_Engine_Design_Specification.md`](../architecture/06_Analytics_Engine_Design_Specification.md). Keep in sync with the governing specification and with [`ADR-0006-Analytics-Engine.md`](../adr/ADR-0006-Analytics-Engine.md).*
