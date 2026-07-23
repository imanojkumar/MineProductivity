# Package Tutorial 7 — Analytics (Deep)

!!! abstract "Milestone 2 · Package Tutorials · Tutorial 7 of 13"
    Deep, full-surface tutorial for `mineproductivity.analytics` — the layer that
    *characterises* governed KPI history (is it drifting? how confident are we?)
    **without ever re-deriving the KPI**. Authored to **Package Tutorial Template
    v1.0** under the [Package Tutorial Implementation Standard](../../learning/PACKAGE_TUTORIAL_IMPLEMENTATION_STANDARD.md).

## Objective

Master the working surface of `mineproductivity.analytics`: the `AnalyticsModel`
contract and `AnalyticsContext`, the statistical surface
(`describe`/`percentile`/`histogram`/`distribution`/`confidence_interval`), trend
characterisation (`LinearTrendModel` → `TrendResult`), the analytical-function
model families, the pipeline and runners, and — the payoff — **implementing the
interface-only `ForecastingModel`**.

All 53 public symbols (`mineproductivity.analytics.__all__`) are accounted for
under the **coverage convention** (§5): **23 [deep]** / **30 [ref]**. Public APIs
only.

## Prerequisites

- Package Tutorials [1 — Core](01_core.md), [3 — Events](03_events.md),
  [4 — Registry & Plugins](04_registry_and_plugins.md), [6 — KPIs](06_kpis.md):
  analytics consumes KPI results and integrates all of these (§3).
- [Fundamentals L07 — Analytics](../fundamentals/07_analytics.md): the intro —
  characterise without re-deriving, and the per-second slope trap.

This tutorial **builds on** L07.

## Running the examples

Every code block below is executed and its output pasted verbatim. The three
scripts were **authored for this tutorial** (analytics shipped no examples):

```bash
pip install -e .
python examples/analytics/01_describe_and_distribution.py   # ...and 02, 03
```

---

## 1. Why this package exists

A KPI tells you *what* a number is; something has to say whether it is **drifting,
normal, or anomalous** — and to do so *without* recomputing the metric with a
slightly different definition. That is `analytics`. It takes governed `KPIResult`
history as a `TimeSeries` and characterises it: the distribution (not just the
mean), a trend with a goodness-of-fit, a baseline, a benchmark band.

Its discipline is the platform's spine applied one layer up: **characterise, never
re-derive.** If `PROD.TPH` says 1,150 t/h, analytics takes that number — it does
not reopen the event store and recompute tonnes ÷ hours. And where a *modelling*
decision is genuinely yours (which forecasting algorithm?), the package **ships
nothing** and hands you a stable contract instead (ADR-0006).

## 2. Architectural role

`analytics` sits above `kpis`, below `decision`:

```
… kpis ─► analytics ─► decision ─► digital_twin ─► …
```

It reads the governed evidence `kpis` produces and emits *characterisations*
(`TrendResult`, `Baseline`, `BenchmarkResult`, …) that `decision` acts on. It
derives nothing the KPI layer already governs.

## 3. Integration with adjacent layers

**`kpis` (Tutorial 6) — the input:** `TimeSeries.from_kpi_results(...)` builds a
series straight from `KPIResult`s, and `AnalyticsContext` can carry a `KPIEngine`.
Analytics **consumes** the governed metric; it never re-derives it.

**`events` (Tutorial 3):** `AnalyticsContext.event_store` and
`TimeSeries.from_event_query(...)` let a model read the log when it genuinely needs
raw observations rather than KPI outputs.

**`registry` (Tutorial 4):** `REGISTRY` is a `registry.Registry`; `@register` adds
a model, and `AnalyticsVersionConflictError` guards duplicate codes.

**`core` (Tutorial 1):** every result (`AnalyticsResult` and its subtypes),
`TimeSeries`/`TimeSeriesPoint` are `core.BaseValueObject`s; `AnalyticsMetadata`
subclasses `core.BaseMetadata`.

**Upward:** `decision` consumes `TrendResult`/`Baseline`/`BenchmarkResult` as
evidence — this package produces the *characterisation* the decision layer reasons
over.

## 4. Package structure

Analytics organises by **analytical function**, not mining domain.

| Group | Module(s) | Public symbols |
|---|---|---|
| The model contract | `abstractions` | `AnalyticsModel`, `AnalyticsContext` |
| Metadata & registry | `metadata`, `_registry` | `AnalyticsMetadata`, `AnalyticsCategory`, `REGISTRY`, `register` |
| Time series | `timeseries`, `windowing` | `TimeSeries`, `TimeSeriesPoint`, `RollingSpec` |
| Statistics | `statistics` | `describe`, `percentile`, `histogram`, `distribution`, `confidence_interval` |
| Results | `result` | `AnalyticsResult`, `StatisticalSummary`, `TrendResult`, `DistributionSummary`, `Histogram`, `ConfidenceInterval`, `Baseline`, `BenchmarkResult`, `ForecastResult`, `DataQualityScore`, `AnomalyFlag`, `OutlierFlag` |
| Model families | `trend`, `baseline`, `benchmarking`, `forecasting`, `anomaly`, `outliers` | `TrendModel`, `LinearTrendModel`, `BaselineModel`, `RollingBaselineModel`, `BenchmarkModel`, `BandBenchmarkModel`, `ForecastingModel`, `AnomalyDetector`, `OutlierDetector` |
| Rolling & aggregation | `rolling`, `aggregation` | `rolling_mean`, `rolling_std`, `rolling_apply`, `AggregationEngine`, `GroupBySpec` |
| Pipeline & runners | `pipeline`, `batch`, `streaming`, `incremental`, `quality` | `AnalyticsPipeline`, `PipelineStage`, `ModelStage`, `DataQualityStage`, `BatchAnalyticsRunner`, `StreamingAnalyticsSession`, `IncrementalAccumulator`, `DataQualityScorer`, `MissingDataPolicy` |
| Exceptions | `exceptions` | `InsufficientDataError`, `AnalyticsModelNotFoundError`, `AnalyticsValidationError`, `AnalyticsVersionConflictError` |

## 5. Public APIs

All 53 exports under the **coverage convention**:

**The spine, statistics & trend — [deep]**
: `AnalyticsModel`, `AnalyticsContext`, `AnalyticsMetadata`, `AnalyticsCategory`,
  `AnalyticsResult`, `TimeSeries`, `TimeSeriesPoint`, `describe`,
  `StatisticalSummary`, `percentile`, `histogram`, `Histogram`, `distribution`,
  `DistributionSummary`, `confidence_interval`, `ConfidenceInterval`, `TrendModel`,
  `LinearTrendModel`, `TrendResult`, `ForecastingModel`, `ForecastResult`,
  `REGISTRY`, `register`

**Everything else — [ref]** — see the table.

### Reference coverage

| Group | Symbols (`[ref]`) | What / when |
|---|---|---|
| Baseline & benchmark | `BaselineModel`, `RollingBaselineModel`, `Baseline`, `BenchmarkModel`, `BandBenchmarkModel`, `BenchmarkResult` | "Normal-range" models (a rolling baseline band) and benchmark-band classification — each an `AnalyticsModel` you extend exactly as §13 extends `ForecastingModel`. |
| Anomaly & outlier | `AnomalyDetector`, `AnomalyFlag`, `OutlierDetector`, `OutlierFlag` | Interface-only detectors (ship no algorithm, by design) and their flag result types. |
| Rolling & aggregation | `rolling_mean`, `rolling_std`, `rolling_apply`, `RollingSpec`, `AggregationEngine`, `GroupBySpec` | Windowed rolling functions and grouped aggregation over a series. |
| Pipeline & runners | `AnalyticsPipeline`, `PipelineStage`, `ModelStage`, `DataQualityStage`, `BatchAnalyticsRunner`, `StreamingAnalyticsSession`, `IncrementalAccumulator` | Compose models into a staged pipeline; run it batch, streaming, or incrementally. |
| Data quality | `DataQualityScorer`, `DataQualityScore`, `MissingDataPolicy` | Score completeness/validity of a series and decide how to treat gaps. |
| Exceptions | `InsufficientDataError`, `AnalyticsModelNotFoundError`, `AnalyticsValidationError`, `AnalyticsVersionConflictError` | Too few observations, unknown model code, invalid metadata, duplicate registration. All derive from `core.MineProductivityError`. |

## 6. Conceptual model

Five ideas explain the package.

**A. An analytics model is metadata + one pure function.** `AnalyticsModel`
declares `meta: AnalyticsMetadata` and implements `_analyze(series, *, context) ->
AnalyticsResult` — the exact "as-object" shape `kpis.BaseKPI` established one layer
down.

**B. Qualify, don't coerce.** `analyze` checks `meta.min_observations` first; too
few observations returns an `AnalyticsResult` carrying a warning, never a crash and
never a fabricated result.

**C. Organised by analytical function.** Not by mining namespace (that is `kpis`'
job) but by *what the analysis does*: trend, baseline, benchmark, forecasting,
anomaly, outlier. Every family shares the one `AnalyticsModel` abstraction.

**D. The mean is the least interesting number.** `describe` returns a
*distribution* (spread, percentiles), and `LinearTrendModel` a *fit* (slope +
`r_squared`) — because an average hides a drift, and a `decreasing` direction with
`r² = 0.04` is noise wearing a trend's clothes.

**E. Modelling decisions are refused, on purpose.** `ForecastingModel`,
`AnomalyDetector`, and `OutlierDetector` ship **zero** implementations. Choosing an
algorithm is your call; the package gives you a stable contract to plug into
(ADR-0006).

## 7. Real mining examples

The walkthroughs characterise a fleet's `PROD.TPH` over 14 shifts as it drifts from
1,310 down to 1,150 t/h: its distribution, its linear trend, and a custom
drift-forecast of the next three shifts (§13).

## 8. Step-by-step walkthroughs

### 8.1 The distribution, not just the mean

`describe(series)` returns a `StatisticalSummary` (n, mean, std, range,
percentiles); `distribution(...)` adds shape (skewness, kurtosis); `percentile` and
`histogram` complete the picture. Running
[`01_describe_and_distribution.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/analytics/01_describe_and_distribution.py):

```text
--- describe(): the distribution, not just the average ---
n=14 mean=1247.7 std=45.3 range=1150->1310
percentiles available: [50, 90, 99]

--- the mean is the least interesting number ---
mean 1248 t/h looks healthy, but the fleet is travelling 1310 -> 1150

--- distribution(): shape (skewness, kurtosis) ---
skewness=-0.586 kurtosis=-0.502

--- percentile() and histogram() over the raw values ---
p25=1223  p75=1285
histogram counts across 4 bins: (2, 2, 5, 5)
```

`mean = 1,248 t/h` looks fine against a target — but the fleet is *travelling* from
1,310 to 1,150. The mean is an artefact of a trend; the spread is the story.

### 8.2 Trend: turning "looks worse" into a defensible judgement

`LinearTrendModel().analyze(series, context=...)` returns the `AnalyticsResult`
family; narrow it to `TrendResult` for `direction`/`slope`/`r_squared`. The slope
is fitted in **elapsed seconds** — convert before showing a human. Running
[`02_trend.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/analytics/02_trend.py):

```text
--- A trend model characterises the observed window ---
direction='decreasing'  r_squared=0.9530

--- Mind the units: the raw slope is per SECOND ---
slope = -0.000254 t/h per second  <-- the raw fit unit
      = -11.0 t/h per 12 h shift  <-- what a human asks for

reading: losing ~11.0 t/h every shift; r^2=0.953 means a straight line explains the decline well -- degradation, not noise.
```

`-0.000254` printed raw reads like "no trend"; converted it is "**−11 t/h every
shift**", and `r² = 0.95` says the decline is real. Noticing that the raw unit is
per-second is the skill L07 drilled — and `AnalyticsContext(event_store=...)` is
required even for a pure-series model, because the contract is uniform.

### 8.3 The refusal made concrete — and its extension seam

`describe` and `LinearTrendModel` characterise the *observed window*; they never
extrapolate. Forecasting the *future* is a modelling decision the package refuses
to make, so `ForecastingModel` ships as an interface-only contract. §13 implements
it.

## 9. Repository example reuse

All three `analytics` scripts were **authored for this tutorial** (the package had
no examples — Standard §1 / Risk R2) and added to the shared smoke test. Each
executed (exit `0`), output above.

| Script | Public API it exercises | Walkthrough |
|---|---|---|
| [`01_describe_and_distribution.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/analytics/01_describe_and_distribution.py) | `TimeSeries`, `describe`, `StatisticalSummary`, `distribution`, `percentile`, `histogram` | §8.1 |
| [`02_trend.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/analytics/02_trend.py) | `LinearTrendModel`, `TrendResult`, `AnalyticsContext` | §8.2 |
| [`03_plugin_forecasting_model.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/analytics/03_plugin_forecasting_model.py) | `ForecastingModel`, `ForecastResult`, `ConfidenceInterval`, `AnalyticsMetadata`, `register` | §13 |

## 10. Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| Re-deriving the KPI inside analytics | Two definitions of one metric | Consume the `KPIResult`/`TimeSeries` |
| Reporting `slope` raw | `-0.00` reads as "no trend" while the fleet degrades | Convert to per-shift (× 12 × 3600) |
| Trusting `direction` without `r_squared` | `decreasing` can be pure noise | Check `r_squared` too |
| Reporting only the mean | Hides a drift behind a reassuring average | Report the distribution |
| Expecting a built-in forecaster | `ForecastingModel` has zero implementations | Register a plugin (ADR-0006) |
| Raising from `_analyze` on a short series | One thin window crashes a batch | Return a warning-carrying result; `analyze` guards `min_observations` |

## 11. Best practices

- **Feed analytics from governed KPI results**, not raw rows you re-derived.
- **Always convert the slope** to an operational unit before showing a human.
- **Report the spread, not just the mean**; check `r_squared` before believing a direction.
- **Keep `_analyze` pure and stateless** (safe to share across threads).
- **Reach for a plugin** for forecasting/anomaly/outlier — the contracts are waiting.

## 12. Performance considerations

- **Statistics are single-pass** where possible; `describe`/`distribution` compute
  their summaries in one scan of the values.
- **`IncrementalAccumulator` and `StreamingAnalyticsSession`** update as new points
  arrive, avoiding a full recompute — for live characterisation off the event bus.
- **`BatchAnalyticsRunner`** amortises setup across many series.
- **Models are stateless** across `analyze` calls — safe to share and parallelise.

## 13. Extension points — implement a `ForecastingModel`

`analytics` ships **zero** forecasters (ADR-0006). The extension point is to
implement the interface-only contract: subclass `ForecastingModel`, declare
`AnalyticsMetadata`, implement `_forecast(series, *, horizon, context) ->
ForecastResult`, and `@register`. The example was executed and passes `ruff` /
`ruff format --check` / `mypy --strict`:

```python
from typing import ClassVar
from statistics import fmean, pstdev

from mineproductivity.analytics import (
    AnalyticsCategory, AnalyticsContext, AnalyticsMetadata, ConfidenceInterval,
    ForecastingModel, ForecastResult, TimeSeries, register,
)


@register
class DriftForecaster(ForecastingModel):
    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="FORECAST.Drift", name="Linear Drift Forecaster",
        category=AnalyticsCategory.FORECASTING,
        description="Naive drift forecast: last value + mean step, +/- 2 std band.",
        min_observations=2,
    )

    def _forecast(self, series: TimeSeries, *, horizon: int, context: AnalyticsContext) -> ForecastResult:
        values = series.values()
        drift = fmean([b - a for a, b in zip(values, values[1:])]) if len(values) > 1 else 0.0
        spread = pstdev(values) if len(values) > 1 else 0.0
        predicted = tuple(values[-1] + drift * (s + 1) for s in range(horizon))
        intervals = tuple(
            ConfidenceInterval(model_code=self.meta.code, lower=p - 2 * spread,
                               upper=p + 2 * spread, confidence=0.95, method="normal")
            for p in predicted
        )
        return ForecastResult(model_code=self.meta.code, horizon=horizon,
                              predicted=predicted, intervals=intervals)
    # _analyze (abstract from AnalyticsModel) delegates to _forecast(horizon=1).
```

Exercising it — the plugin registers, forecasts three shifts with 95% bands, and
inherits the qualify-don't-coerce guard for a too-short series:

```text
--- analytics ships zero forecasters; this plugin implements the contract ---
'FORECAST.Drift' in REGISTRY: True

--- Forecast the next 3 shifts, each a point estimate + 95% band ---
  shift +1: 1138 t/h  [1047, 1228] (normal)
  shift +2: 1125 t/h  [1035, 1216] (normal)
  shift +3: 1113 t/h  [1023, 1204] (normal)

--- analyze() inherits the qualify-don't-coerce guard for short series ---
1-point series -> warnings=('insufficient data: 1 observations, 2 required',)
```

The same idiom implements a **`BaselineModel`**, **`BenchmarkModel`**,
**`AnomalyDetector`**, or **`OutlierDetector`** — every analytical function is an
`AnalyticsModel` you subclass and register, shipped as a plugin (Tutorial 4).

!!! note "The refusal is the feature"
    Trend characterises what *happened*; it never extrapolates. Forecasting,
    anomaly, and outlier detection ship no algorithm because the right one depends
    on your data and horizon — a generic default would be a false promise. The
    stable contract lets your plugin slot in without a framework change.

## 14. Exercises

1. **Hide a trend behind a mean.** Build a series whose mean is exactly on target but
   which falls from 1,400 to 1,100. What does `describe` reveal that the mean conceals?
2. **Convert the slope.** Take a `TrendResult.slope` and compute the loss per shift,
   per day, and per 14-shift roster. Which number goes in a shift report?
3. **Manufacture noise.** Replace the series with 14 random values; what happens to
   `direction` and, crucially, to `r_squared`? What r² would you require to escalate?
4. **Implement a baseline.** Sketch a `BaselineModel` that returns a `Baseline` band
   (mean ± 2 std) over a rolling window. Which abstract method do you implement?
5. **Forecast, then reflect.** Extend `DriftForecaster` to a 6-shift horizon; why do
   the confidence bands *not* widen with horizon here, and why is that a limitation a
   better model would fix?

## 15. Reference solutions

??? success "Solution 1 — Hide a trend behind a mean"
    ```python
    from mineproductivity.analytics import describe
    s = describe(series_from([1400, 1350, 1300, 1250, 1200, 1150, 1100]))
    s.mean       # ~1250 (on target)
    s.minimum, s.maximum   # 1100, 1400 -- the drift the mean hides
    ```

??? success "Solution 2 — Convert the slope"
    ```python
    per_shift = result.slope * 12 * 3600
    per_day   = result.slope * 24 * 3600
    over_roster = per_shift * (len(series) - 1)
    ```
    The **per-shift** figure is what a superintendent acts on; `slope` in
    t/h-per-second is not.

??? success "Solution 3 — Manufacture noise"
    `direction` becomes whatever the random walk happened to do, but `r_squared`
    collapses toward 0. A `decreasing` direction with r² ≈ 0.05 is noise; require a
    high r² (say ≥ 0.7) before treating a trend as actionable.

??? success "Solution 4 — Implement a baseline"
    You implement `_analyze` (from `AnalyticsModel`), returning a `Baseline` with
    `mean`, `std`, `lower`, `upper`, and its `RollingSpec` — the same "declare meta,
    implement one method, register" shape as the forecaster.

??? success "Solution 5 — Forecast, then reflect"
    The bands are a flat `± 2·pstdev(history)` regardless of `step`, so they do not
    widen with horizon. A real forecaster propagates uncertainty forward (the band
    should grow the further out you predict) — exactly the kind of modelling nuance
    the platform refuses to hard-code, leaving it to your plugin.

## 16. Further reading

- **[`analytics` package guide](../../packages/analytics.md)** — the capability-tour view.
- **[`analytics` API reference](../../api-reference/analytics.md)** — every symbol, from source.
- **[Analytics Engine Design Specification](../../architecture/06_Analytics_Engine_Design_Specification.md)** · **[ADR-0006](../../adr/ADR-0006-Analytics-Engine.md)** — why no forecaster ships, the model-as-object shape.
- **[Fundamentals L07 — Analytics](../fundamentals/07_analytics.md)** · Package Tutorial [6 — KPIs](06_kpis.md).

---

**Next package tutorial:** Decision (deep) — turning a measured drift into an
explained, audited recommendation.
*(Not yet written — Tutorial 8 of 13.)*
