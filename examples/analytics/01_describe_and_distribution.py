"""Characterise a KPI's shift history: describe(), distribution(),
percentile(), histogram() -- the spread and shape, not just the mean.

Run: python examples/analytics/01_describe_and_distribution.py
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from mineproductivity.analytics import (
    TimeSeries,
    TimeSeriesPoint,
    describe,
    distribution,
    histogram,
    percentile,
)

_SHIFT_START = datetime(2026, 6, 12, 6, tzinfo=timezone.utc)
# A fleet's PROD.TPH (t/h) drifting down across 14 shifts.
_TPH = (1310, 1300, 1295, 1288, 1276, 1265, 1258, 1249, 1240, 1232, 1220, 1205, 1180, 1150)


def _series() -> TimeSeries:
    return TimeSeries(
        points=tuple(
            TimeSeriesPoint(timestamp=_SHIFT_START + timedelta(hours=12 * i), value=float(v))
            for i, v in enumerate(_TPH)
        )
    )


def main() -> None:
    series = _series()

    print("--- describe(): the distribution, not just the average ---")
    summary = describe(series)
    print(
        f"n={summary.n} mean={summary.mean:.1f} std={summary.std:.1f} "
        f"range={summary.minimum:.0f}->{summary.maximum:.0f}"
    )
    print(f"percentiles available: {sorted(summary.percentiles)}")

    print()
    print("--- the mean is the least interesting number ---")
    print(
        f"mean {summary.mean:.0f} t/h looks healthy, but the fleet is travelling "
        f"{summary.maximum:.0f} -> {summary.minimum:.0f}"
    )

    print()
    print("--- distribution(): shape (skewness, kurtosis) ---")
    dist = distribution(series.values())
    print(f"skewness={dist.skewness:.3f} kurtosis={dist.kurtosis:.3f}")

    print()
    print("--- percentile() and histogram() over the raw values ---")
    print(f"p25={percentile(series.values(), 25):.0f}  p75={percentile(series.values(), 75):.0f}")
    hist = histogram(series.values(), bins=4)
    print(f"histogram counts across 4 bins: {hist.counts}")


if __name__ == "__main__":
    main()
