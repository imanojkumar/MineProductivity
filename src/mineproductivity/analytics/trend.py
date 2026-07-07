"""Deterministic trend fitting over a ``TimeSeries`` (§14).

``LinearTrendModel`` characterizes an observed series' direction and fit
quality only -- it never extrapolates beyond the observed window (that
is forecasting, §16, a separate, interface-only concern this module
does not implement).
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar, Literal

from mineproductivity.analytics._registry import register
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import TrendResult
from mineproductivity.analytics.statistics import _mean, _population_variance
from mineproductivity.analytics.timeseries import TimeSeries
from mineproductivity.analytics.windowing import RollingSpec

__all__ = ["LinearTrendModel", "TrendModel"]


class TrendModel(AnalyticsModel, ABC):
    """Category base for trend-fitting strategies."""


@register
class LinearTrendModel(TrendModel):
    """The default, concrete trend strategy: ordinary-least-squares
    linear fit over a ``TimeSeries``' (timestamp, value) pairs. Fully
    deterministic and closed-form -- no forecasting, no extrapolation
    beyond the observed window.

    Registered into ``analytics.REGISTRY`` at import time (§32-33),
    mirroring how ``kpis.standard_library`` self-registers.

    Examples
    --------
    >>> from datetime import datetime, timedelta, timezone
    >>> from mineproductivity.analytics.timeseries import TimeSeriesPoint
    >>> from mineproductivity.events.store import _InMemoryEventStore
    >>> start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    >>> series = TimeSeries(points=tuple(
    ...     TimeSeriesPoint(timestamp=start + timedelta(days=i), value=float(i))
    ...     for i in range(5)
    ... ))
    >>> context = AnalyticsContext(event_store=_InMemoryEventStore())
    >>> result = LinearTrendModel().analyze(series, context=context)
    >>> result.direction
    'increasing'
    >>> round(result.r_squared, 4)
    1.0
    """

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="TREND.Linear",
        category=AnalyticsCategory.TREND,
        description="Ordinary least squares linear trend fit.",
        min_observations=2,
    )

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> TrendResult:
        points = series.points
        origin = points[0].timestamp
        x_values = [(point.timestamp - origin).total_seconds() for point in points]
        y_values = list(series.values())

        mean_x = _mean(x_values)
        mean_y = _mean(y_values)
        # Sxx is the raw sum of squared deviations OLS's slope formula
        # needs, i.e. n times the population variance already computed
        # by statistics.py -- reused here instead of re-deriving the
        # same sum-of-squared-deviations formula a second time.
        ss_xx = _population_variance(x_values, mean=mean_x) * len(x_values)

        if ss_xx == 0.0:
            # Every observation shares the same timestamp -- no time
            # variation to fit a slope against. "Qualify, don't coerce"
            # (§8, §34): report a flat, zero-confidence trend with a
            # warning rather than raising ZeroDivisionError.
            return TrendResult(
                model_code=self.meta.code,
                warnings=("all observations share the same timestamp; trend is undefined",),
                slope=0.0,
                intercept=mean_y,
                r_squared=0.0,
                direction="flat",
                window=RollingSpec(periods=len(points)),
            )

        ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values, strict=True))
        slope = ss_xy / ss_xx
        intercept = mean_y - slope * mean_x

        ss_tot = _population_variance(y_values, mean=mean_y) * len(y_values)
        if ss_tot == 0.0:
            # Every observation has the same value -- the flat line
            # mean_y = intercept fits perfectly (0 unexplained variance
            # out of 0 total variance): a perfect, trivial fit.
            r_squared = 1.0
        else:
            ss_res = sum(
                (y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values, strict=True)
            )
            r_squared = 1.0 - ss_res / ss_tot

        direction: Literal["increasing", "decreasing", "flat"]
        if slope > 0.0:
            direction = "increasing"
        elif slope < 0.0:
            direction = "decreasing"
        else:
            direction = "flat"

        return TrendResult(
            model_code=self.meta.code,
            slope=slope,
            intercept=intercept,
            r_squared=r_squared,
            direction=direction,
            window=RollingSpec(periods=len(points)),
        )
