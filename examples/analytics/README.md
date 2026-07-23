# Examples - mineproductivity.analytics

## Purpose

Runnable, minimal, self-contained scripts demonstrating the analytics layer:
characterising a KPI's history (statistics and trend) **without re-deriving the
KPI**, and implementing the interface-only `ForecastingModel` extension point.

## Scope

Example scripts and their direct output. No test assertions live here (see
`tests/unit/analytics/`); each script is meant to be read and run by a human.

## Contents

- `01_describe_and_distribution.py` - `describe()`, `distribution()`,
  `percentile()`, `histogram()` over a `TimeSeries`: the spread and shape, not
  just the mean.
- `02_trend.py` - `LinearTrendModel` -> `TrendResult` (direction, slope,
  r_squared) and the per-second slope-unit trap.
- `03_plugin_forecasting_model.py` - the extension point: a naive drift
  `ForecastingModel` implementing the interface-only contract and registering,
  producing a `ForecastResult`.

## Dependencies

Only `mineproductivity` itself (editable-installed from this repository). No
third-party packages.

## Running

```bash
python examples/analytics/01_describe_and_distribution.py
python examples/analytics/02_trend.py
python examples/analytics/03_plugin_forecasting_model.py
```

Each script exits `0` and prints its own narrated output.
