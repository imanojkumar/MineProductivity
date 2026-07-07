# mineproductivity.analytics

## Purpose

Statistical and analytical processing built on top of KPI and event data — trend analysis, correlation, and descriptive analytics.

## Scope

**What belongs here:**
- Analytical model interfaces and pipeline contracts.
- Descriptive/statistical analysis built strictly on `kpis` and `events` outputs.

**What must never belong here:**
- Optimization or prescriptive logic (see `optimization`, `decision`).
- Direct connector or I/O access — analytics consumes projections, not raw sources.

## Responsibilities

- Implements the `analytics` subsystem as defined in the Reference Implementation Blueprint v1.0.
- Implements the full module list from design spec §6: the **Analytics Foundation** (entities,
  value objects, metadata, enums, exception hierarchy), **Metric Pipelines & Aggregation**,
  **Statistical Primitives**, **Rolling Analytics**, **Trend Analysis**, **Baseline Analysis**,
  **Benchmark Analysis**, **Data Quality & Missing Data Handling**, all three interface-only
  extension points -- the **Forecasting Framework**, the **Anomaly Detection Framework**, and the
  **Outlier Detection Framework** -- all three **Execution Modes** (batch, streaming,
  incremental) slices, and the **Registry & Plugin Framework** (§32–§33). `ForecastingModel`,
  `AnomalyDetector`, and `OutlierDetector` each ship zero concrete subclasses by design
  (ADR-0006) -- choosing a forecasting, anomaly-detection, or outlier-detection algorithm is a
  modeling decision outside this package's charter, left for a future, independently-versioned
  plugin. `BatchAnalyticsRunner` is a thin, named wrapper over `AnalyticsPipeline.run`;
  `StreamingAnalyticsSession` subscribes to an `events.EventBus` and incrementally updates one or
  more `IncrementalAccumulator`s per tracked payload field, one `threading.Lock` per accumulator
  key serializing concurrent updates to that key; `IncrementalAccumulator` implements Welford's
  online algorithm for O(1)-update, O(1)-memory streaming mean/variance/min/max (`percentiles`
  is always empty in its `StatisticalSummary` -- a genuine, disclosed limitation of O(1)-memory
  streaming computation, not an oversight). `REGISTRY`/`register` (`_registry.py`) specialize
  `registry.Registry` exactly as `kpis._registry` does one layer down, add-only keyed by
  `AnalyticsMetadata.code`; `LinearTrendModel`, `RollingBaselineModel`, and `BandBenchmarkModel`
  are all `@register`-decorated and discoverable via `REGISTRY` at import time.
  `AggregationEngine.reduce()` is fully implemented: it groups a plain numeric `TimeSeries` by
  scope field(s) and reuses `describe()` verbatim per group, deriving `sum`/`mean`/`median` from
  the returned `StatisticalSummary` (see its own docstring for the full explanation). Every
  module described in design spec §6 is now implemented.

## Contents

- `__init__.py` — public API surface (53 symbols).
- `_registry.py` — `REGISTRY`, `register` (plugin registration, §32–§33).
- `abstractions.py` — `AnalyticsModel` (ABC), `AnalyticsContext`.
- `metadata.py` — `AnalyticsMetadata`, `AnalyticsCategory`.
- `result.py` — `AnalyticsResult` and every concrete result/flag type.
- `timeseries.py` — `TimeSeries`, `TimeSeriesPoint`.
- `windowing.py` — `RollingSpec`.
- `pipeline.py` — `AnalyticsPipeline`, `PipelineStage` (ABC), `ModelStage`.
- `aggregation.py` — `AggregationEngine`, `GroupBySpec`.
- `statistics.py` — `describe`, `percentile`, `histogram`, `distribution`, `confidence_interval`.
- `rolling.py` — `rolling_mean`, `rolling_std`, `rolling_apply`.
- `trend.py` — `TrendModel` (ABC), `LinearTrendModel`.
- `baseline.py` — `BaselineModel` (ABC), `RollingBaselineModel`.
- `benchmarking.py` — `BenchmarkModel` (ABC), `BandBenchmarkModel`.
- `quality.py` — `DataQualityScorer`, `MissingDataPolicy` (enum), `DataQualityStage`.
- `forecasting.py` — `ForecastingModel` (ABC, interface only -- zero concrete subclasses).
- `anomaly.py` — `AnomalyDetector` (ABC, interface only -- zero concrete subclasses).
- `outliers.py` — `OutlierDetector` (ABC, interface only -- zero concrete subclasses).
- `batch.py` — `BatchAnalyticsRunner`.
- `streaming.py` — `StreamingAnalyticsSession`.
- `incremental.py` — `IncrementalAccumulator`.
- `exceptions.py` — the package's exception hierarchy.
- `README.md` — this file.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`, `plugins`, `kpis`. (`connectors` is a permitted import under the platform-wide layering rule but is not exercised — analytics operates on already-computed `KPIResult`s, never a vendor-specific wire format.)

**Depended on by:** `decision`, `digital_twin`, `simulation`, `optimization`, `agents`, `visualization`

## Future Work

Every module in design spec §6 is now implemented; no further `src/mineproductivity/analytics/`
implementation work is outstanding. Concrete forecasting, anomaly-detection, and
outlier-detection algorithms remain deliberately unimplemented (ADR-0006) -- each is an
independently-versioned plugin decision for a future package, not a gap in this one. The
worked examples under `examples/analytics/` and the benchmark reports under
`benchmark/reports/analytics/` are outside this package's own source/test/README boundary and
were treated as out of scope for this milestone.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
