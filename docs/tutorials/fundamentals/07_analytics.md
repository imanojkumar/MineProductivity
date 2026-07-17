# Lesson 07 - Analytics

## Objective

Characterise a fleet's governed KPI history - is it normal, is it drifting, how confident are we - **without ever re-deriving the KPI itself**.

## Prerequisites

- [Lesson 06 - KPIs](06_kpis.md) (analytics consumes governed KPI results; you must know what makes them governed)

## Concepts covered

| Concept | Why it exists |
|---|---|
| `TimeSeries` / `TimeSeriesPoint` | A sequence of governed facts over time. |
| `describe()` → `StatisticalSummary` | `n`, `mean`, `std`, `minimum`, `maximum`, `percentiles` - the spread, not just the average. |
| `LinearTrendModel` → `TrendResult` | Turns "looks worse" into `direction`, `slope`, `r_squared`. |
| **No re-derivation** | Analytics reads `KPIResult`s. It never recomputes tonnes ÷ hours. |
| Interface-only forecasting | `ForecastingModel` ships **zero** implementations, on purpose. |

## Complete runnable example

**[:material-file-code: `examples/fundamentals/07_analytics/analytics.py`](https://github.com/imanojkumar/MineProductivity/blob/main/examples/fundamentals/07_analytics/analytics.py)**

```bash
python examples/fundamentals/07_analytics/analytics.py
```

Every point comes *out of the KPI object* - analytics derives nothing:

```python
from mineproductivity.analytics import (
    AnalyticsContext, LinearTrendModel, TimeSeries, TimeSeriesPoint, TrendResult, describe,
)
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import REGISTRY

tph_kpi = REGISTRY.get("PROD.TPH")()
points = [
    TimeSeriesPoint(timestamp=..., value=tph_kpi.compute([{...}]).value)
    for tonnes, hours in SHIFT_LOG
]
series = TimeSeries(points=tuple(points))

summary = describe(series)

# analyze() is the PUBLIC contract. It returns the AnalyticsResult family,
# so narrow to TrendResult to read slope / direction / r_squared.
analysed = LinearTrendModel().analyze(
    series, context=AnalyticsContext(event_store=_InMemoryEventStore())
)
assert isinstance(analysed, TrendResult)
trend = analysed
```

## Expected output

```text
--- 1. Start from GOVERNED facts, not raw arithmetic ---
built a 14-shift TimeSeries of PROD.TPH for FL-NORTH
first shift 1,300.0 t/h -> last shift 1,150.0 t/h
(every point came out of the KPI object -- analytics re-derived nothing)

--- 2. describe(): characterise the distribution ---
n       : 14 shifts
mean    : 1,234.3 t/h
std     : 50.8 t/h
range   : 1,150.0 -> 1,310.0 t/h
p50     : 1,235.0 t/h
p90     : 1,297.0 t/h
(a mean alone hides the story; the spread is the operational question)

--- 3. A trend model turns 'looks worse' into a defensible judgement ---
model     : TREND.Linear
direction : decreasing
r_squared : 0.9740
slope     : -0.000288 t/h per SECOND  <-- the raw fit unit
            = -12.4 t/h per 12 h shift  <-- what a human asks for

reading   : FL-NORTH is losing ~12.4 t/h every shift
            (~162 t/h across the 14-shift window),
            and r^2 = 0.974 says a straight line explains
            the decline well -- this is degradation, not noise.

--- 4. Trend characterises the observed window. It does NOT forecast ---
window characterised: 14 shifts
LinearTrendModel describes what HAPPENED. It will not extrapolate,
and the package ships no forecasting algorithm at all:
  analytics.ForecastingModel is an interface with ZERO implementations.
  ADR-0006 rejected shipping one -- choosing exponential smoothing vs
  ARIMA vs anything else is a modelling decision the platform refuses
  to make on your behalf. A forecasting plugin registers against that
  stable contract instead.

--- 5. Why this layering matters ---
PROD.TPH said WHAT the rate was (governed, one definition, one unit).
Analytics said whether it is DRIFTING (characterisation, no re-derivation).
Neither decided what to DO about it -- that is the decision layer, next.
```

## Explanation

### Characterise, never re-derive

This is the layer's whole discipline. If `PROD.TPH` says 1,150 t/h, analytics takes that number. It does **not** open the event store and recompute tonnes ÷ hours with its own slightly-different idea of operating hours. The moment it did, you would have two definitions of TPH in one system and no way to reconcile a report.

So the flow is strictly one-directional: `kpis` produces governed facts → `analytics` characterises them.

### The mean is the least interesting number

Section 2 reports `mean = 1,234.3 t/h`. On its own that looks healthy against a 1,250 target - barely under. But `range = 1,150 → 1,310` and `std = 50.8` tell the real story: the fleet is not sitting at 1,234, it is *travelling* from 1,310 down to 1,150. The mean is an artefact of a trend, and reporting it alone would hide a degrading fleet behind a reassuring average.

That is why `describe()` returns a distribution, not a number.

### Mind the units - the slope trap

`LinearTrendModel` fits against **elapsed seconds** (`trend.py` computes `x = (timestamp - origin).total_seconds()`). So `slope` is in *t/h per second*: `-0.000288`.

Printed raw at two decimal places that reads `-0.00` - which looks exactly like "no trend at all", while `r² = 0.974` is simultaneously screaming that the decline is almost perfectly linear. Those two statements cannot both be true, and noticing the contradiction is the skill.

Convert to the operational unit:

```python
per_shift = trend.slope * 12 * 3600      # -12.4 t/h per 12 h shift
over_window = per_shift * (len(series.points) - 1)   # ~-162 t/h
```

**FL-NORTH is losing about 12.4 t/h every shift.** That is a sentence a superintendent can act on. `-0.000288` is not.

### Why the platform will not forecast for you

`analytics.ForecastingModel` is an interface with **zero implementations**, and that is deliberate (ADR-0006). Choosing exponential smoothing over ARIMA over a gradient-boosted model is a *modelling* decision that depends on your data, your horizon, and your tolerance for being wrong. The platform refuses to make it on your behalf and pretend it is a framework concern.

Note also that `LinearTrendModel` characterises the **observed window** only. It will not extrapolate. A trend is a description of what happened, not a promise about next week.

## Best practices

- **Always convert the slope to an operational unit** before showing a human. Nobody reasons in t/h-per-second.
- **Report the spread, not just the mean.** `std`, `minimum`, `maximum`, and percentiles are where the story is.
- **Check `r_squared` before believing a `direction`.** A `decreasing` direction with r² = 0.04 is noise wearing a trend's clothes.
- **Feed analytics from governed KPI results**, never from raw rows you re-derived yourself.
- **Reach for a plugin** when you need forecasting - the contract is already there.

## Common mistakes

| Mistake | What happens | Do this instead |
|---|---|---|
| **Reporting `slope` raw** | `-0.00` - you conclude "no trend" while the fleet degrades | Multiply by `12*3600` for per-shift |
| Trusting `direction` alone | `decreasing` can be pure noise | Check `r_squared` too |
| Reporting only the mean | 1,234 looks fine; the fleet is falling from 1,310 to 1,150 | Report the distribution |
| Re-deriving TPH inside analytics | Two definitions of one metric; irreconcilable reports | Consume `KPIResult`s |
| Expecting a built-in forecaster | `ForecastingModel` has no implementations | Register a plugin |
| `AnalyticsContext()` with no store | `event_store` is required | `AnalyticsContext(event_store=_InMemoryEventStore())` |

!!! warning "Exit code 0 is not correctness"
    This lesson's first draft printed `slope: -0.00 t/h per shift` **and exited 0**. It was wrong - mislabelled units - and only reading the output critically caught it. A script that runs is not a script that is right.

## Exercises

1. **Do the unit conversion yourself.** Take the raw slope and compute the loss per shift, per day, and per 14-shift roster. Which is the number you would put in a shift report?
2. **Manufacture noise.** Replace `SHIFT_LOG` with 14 random values between 1,150 and 1,310. What happens to `direction` and, crucially, to `r_squared`? What r² would you personally require before escalating?
3. **Hide a trend behind a mean.** Construct a series whose mean is exactly 1,250 (on target) but which falls from 1,400 to 1,100. What does `describe()` reveal that the mean conceals?
4. **Read the refusal.** Open [`src/mineproductivity/analytics/forecasting.py`](https://github.com/imanojkumar/MineProductivity/blob/main/src/mineproductivity/analytics/forecasting.py). Write down, in your own words, the two reasons ADR-0006 gives for not shipping a forecaster. Do you agree?

## Suggested next lesson

**[Lesson 08 - Decision](08_decision.md)** - the fleet is measurably degrading. Now: does that breach policy, what should we do, and could you defend the call in an incident review six months from now?

---

**See also:** [`analytics` API Reference](../../api-reference/analytics.md) · [`analytics` package guide](../../packages/analytics.md) · [Analytics Engine design specification](../../architecture/06_Analytics_Engine_Design_Specification.md) · [ADR-0006](../../adr/ADR-0006-Analytics-Engine.md)
