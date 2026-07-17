"""Lesson 07 -- Analytics: characterising facts you must never re-derive.

A KPI answers "what was the rate?". Analytics answers the questions a
superintendent actually asks next: *is that normal? is it drifting? how
confident are we?*

The critical discipline here is one line in the architecture: analytics
**reads** already-governed facts and characterises them. It never
recomputes a KPI. If `PROD.TPH` says 1,233 t/h, analytics does not
re-derive tonnes/hours from raw events -- it takes the governed number
and describes its distribution and trend. That is what keeps one number
meaning one thing across the whole platform.

Run: python examples/fundamentals/07_analytics/analytics.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.analytics import (
    AnalyticsContext,
    LinearTrendModel,
    TimeSeries,
    TimeSeriesPoint,
    TrendResult,
    describe,
)
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import REGISTRY

WEEK_START = datetime(2026, 6, 22, 6, 0, tzinfo=timezone.utc)

# Fourteen shifts of the north fleet. Each entry is one shift's governed
# production: tonnes moved and operating hours. Note the slow slide from
# ~1,300 t/h toward ~1,150 t/h -- a real fleet degrading as haul distance
# grows and a shovel starts under-performing.
SHIFT_LOG: list[tuple[float, float]] = [
    (15_600.0, 12.0),
    (15_480.0, 12.0),
    (15_720.0, 12.0),
    (15_360.0, 12.0),
    (15_240.0, 12.0),
    (15_120.0, 12.0),
    (14_880.0, 12.0),
    (14_760.0, 12.0),
    (14_640.0, 12.0),
    (14_400.0, 12.0),
    (14_280.0, 12.0),
    (14_160.0, 12.0),
    (13_920.0, 12.0),
    (13_800.0, 12.0),
]


def main() -> None:
    print("--- 1. Start from GOVERNED facts, not raw arithmetic ---")
    tph_kpi = REGISTRY.get("PROD.TPH")()
    points: list[TimeSeriesPoint] = []
    for index, (tonnes, hours) in enumerate(SHIFT_LOG):
        result = tph_kpi.compute([{"payload_t": tonnes, "operating_h": hours}])
        assert result.value is not None
        points.append(
            TimeSeriesPoint(
                timestamp=WEEK_START + timedelta(hours=12 * index),
                value=result.value,
                scope={"fleet": "FL-NORTH"},
            )
        )
    series = TimeSeries(points=tuple(points))
    print(f"built a {len(series.points)}-shift TimeSeries of PROD.TPH for FL-NORTH")
    print(
        f"first shift {series.points[0].value:,.1f} t/h -> last shift {series.points[-1].value:,.1f} t/h"
    )
    print("(every point came out of the KPI object -- analytics re-derived nothing)")

    print()
    print("--- 2. describe(): characterise the distribution ---")
    summary = describe(series)
    assert summary.mean is not None and summary.std is not None
    print(f"n       : {summary.n} shifts")
    print(f"mean    : {summary.mean:,.1f} t/h")
    print(f"std     : {summary.std:,.1f} t/h")
    print(f"range   : {summary.minimum:,.1f} -> {summary.maximum:,.1f} t/h")
    print(f"p50     : {summary.percentiles[50]:,.1f} t/h")
    print(f"p90     : {summary.percentiles[90]:,.1f} t/h")
    print("(a mean alone hides the story; the spread is the operational question)")

    print()
    print("--- 3. A trend model turns 'looks worse' into a defensible judgement ---")
    context = AnalyticsContext(event_store=_InMemoryEventStore())
    # analyze() is the public contract; it returns the AnalyticsResult family,
    # so narrow to TrendResult to read the trend-specific fields.
    analysed = LinearTrendModel().analyze(series, context=context)
    assert isinstance(analysed, TrendResult)
    trend = analysed
    print(f"model     : {trend.model_code}")
    print(f"direction : {trend.direction}")
    print(f"r_squared : {trend.r_squared:.4f}")

    # MIND THE UNITS. LinearTrendModel fits against elapsed SECONDS
    # (trend.py: x = (timestamp - origin).total_seconds()), so `slope` is
    # "t/h per second" -- a tiny number that prints as -0.00 and looks like
    # "no trend" if you report it raw. Convert to the operational unit.
    seconds_per_shift = 12 * 3600
    per_shift = trend.slope * seconds_per_shift
    over_window = per_shift * (len(series.points) - 1)
    print(f"slope     : {trend.slope:.6f} t/h per SECOND  <-- the raw fit unit")
    print(f"            = {per_shift:,.1f} t/h per 12 h shift  <-- what a human asks for")
    print()
    print(f"reading   : FL-NORTH is losing ~{abs(per_shift):,.1f} t/h every shift")
    print(
        f"            (~{abs(over_window):,.0f} t/h across the {len(series.points)}-shift window),"
    )
    print(f"            and r^2 = {trend.r_squared:.3f} says a straight line explains")
    print("            the decline well -- this is degradation, not noise.")

    print()
    print("--- 4. Trend characterises the observed window. It does NOT forecast ---")
    print(f"window characterised: {len(series.points)} shifts")
    print("LinearTrendModel describes what HAPPENED. It will not extrapolate,")
    print("and the package ships no forecasting algorithm at all:")
    print("  analytics.ForecastingModel is an interface with ZERO implementations.")
    print("  ADR-0006 rejected shipping one -- choosing exponential smoothing vs")
    print("  ARIMA vs anything else is a modelling decision the platform refuses")
    print("  to make on your behalf. A forecasting plugin registers against that")
    print("  stable contract instead.")

    print()
    print("--- 5. Why this layering matters ---")
    print("PROD.TPH said WHAT the rate was (governed, one definition, one unit).")
    print("Analytics said whether it is DRIFTING (characterisation, no re-derivation).")
    print("Neither decided what to DO about it -- that is the decision layer, next.")


if __name__ == "__main__":
    main()
