"""Turn "looks worse" into a defensible judgement: LinearTrendModel ->
TrendResult (direction, slope, r_squared), and the per-second slope trap.

Run: python examples/analytics/02_trend.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.analytics import (
    AnalyticsContext,
    LinearTrendModel,
    TimeSeries,
    TimeSeriesPoint,
    TrendResult,
)
from mineproductivity.events.store import _InMemoryEventStore

_SHIFT_START = datetime(2026, 6, 12, 6, tzinfo=timezone.utc)
_TPH = (1310, 1300, 1295, 1288, 1276, 1265, 1258, 1249, 1240, 1232, 1220, 1205, 1180, 1150)


def main() -> None:
    series = TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=_SHIFT_START + timedelta(hours=12 * i), value=float(v))
            for i, v in enumerate(_TPH)
        )
    )

    # analyze() returns the AnalyticsResult family; narrow to TrendResult.
    context = AnalyticsContext(event_store=_InMemoryEventStore())
    result = LinearTrendModel().analyze(series, context=context)
    assert isinstance(result, TrendResult)

    print("--- A trend model characterises the observed window ---")
    print(f"direction={result.direction!r}  r_squared={result.r_squared:.4f}")

    print()
    print("--- Mind the units: the raw slope is per SECOND ---")
    print(f"slope = {result.slope:.6f} t/h per second  <-- the raw fit unit")
    per_shift = result.slope * 12 * 3600
    print(f"      = {per_shift:.1f} t/h per 12 h shift  <-- what a human asks for")

    print()
    print(
        f"reading: losing ~{abs(per_shift):.1f} t/h every shift; r^2={result.r_squared:.3f} "
        "means a straight line explains the decline well -- degradation, not noise."
    )


if __name__ == "__main__":
    main()
