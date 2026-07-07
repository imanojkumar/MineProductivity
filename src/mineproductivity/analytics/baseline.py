"""Self-referential historical-norm computation over a ``TimeSeries`` (§15).

Distinct from ``benchmarking.py`` (§13), which compares against an
externally published target/band: a ``Baseline`` answers "is this
normal for *this* asset/site, historically," never "how does this
compare to the industry." This module computes and exposes the
baseline band; it deliberately does not decide whether any given
observation violates it -- that classification is a future
``AnomalyDetector``/``OutlierDetector`` plugin's job (§18, §19), kept
separate per §3.4.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar

from mineproductivity.analytics._registry import register
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import Baseline
from mineproductivity.analytics.rolling import rolling_mean, rolling_std
from mineproductivity.analytics.statistics import _mean, _population_stdev
from mineproductivity.analytics.timeseries import TimeSeries
from mineproductivity.analytics.windowing import RollingSpec

__all__ = ["BaselineModel", "RollingBaselineModel"]


class BaselineModel(AnalyticsModel, ABC):
    """Category base for self-referential historical-norm computation --
    distinct from ``BenchmarkModel`` (§13), which compares against an
    externally published target/band. A ``Baseline`` answers "is this
    normal for *this* asset/site, historically," not "how does this
    compare to the industry."
    """


@register
class RollingBaselineModel(BaselineModel):
    """The default, concrete baseline strategy: trailing-window mean and
    standard deviation, forming a ``[mean - k*std, mean + k*std]`` band.

    Registered into ``analytics.REGISTRY`` at import time (§32-33),
    mirroring how ``kpis.standard_library`` self-registers.

    Consumes :func:`~mineproductivity.analytics.rolling.rolling_mean`/
    :func:`~mineproductivity.analytics.rolling.rolling_std` directly for
    the trailing-window computation -- no moving-average logic is
    reimplemented here. The returned :class:`~mineproductivity.analytics.result.Baseline`
    reflects the trailing window ending at the series' most recent
    observation (the "current" historical norm); ``rolling.py`` already
    represents "not yet enough trailing history" as an absent point
    rather than a sentinel, so if *no* point in the series has a full
    window (e.g. ``spec.periods`` exceeds the series length beyond what
    ``spec.min_periods`` tolerates), this model falls back to a
    whole-series baseline via :mod:`mineproductivity.analytics.statistics`'s
    own ``_mean``/``_population_stdev`` helpers, with a warning attached
    -- never raises, matching the "qualify, don't coerce" rule already
    governing every ``AnalyticsModel``.

    Examples
    --------
    >>> from datetime import datetime, timedelta, timezone
    >>> from mineproductivity.analytics.timeseries import TimeSeriesPoint
    >>> from mineproductivity.events.store import _InMemoryEventStore
    >>> start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    >>> series = TimeSeries(points=tuple(
    ...     TimeSeriesPoint(timestamp=start + timedelta(days=i), value=10.0)
    ...     for i in range(5)
    ... ))
    >>> model = RollingBaselineModel(spec=RollingSpec(periods=3, min_periods=3))
    >>> context = AnalyticsContext(event_store=_InMemoryEventStore())
    >>> result = model.analyze(series, context=context)
    >>> result.mean, result.lower, result.upper
    (10.0, 10.0, 10.0)
    """

    meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
        code="BASELINE.Rolling",
        category=AnalyticsCategory.BASELINE,
        description="Trailing-window mean/standard-deviation historical-norm band.",
        min_observations=1,
    )

    def __init__(self, *, spec: RollingSpec, k: float = 2.0) -> None:
        self._spec = spec
        self._k = k

    def __repr__(self) -> str:
        return f"{type(self).__name__}(spec={self._spec!r}, k={self._k!r})"

    def _analyze(self, series: TimeSeries, *, context: AnalyticsContext) -> Baseline:
        rolling_means = rolling_mean(series, self._spec)
        if len(rolling_means) == 0:
            return self._whole_series_fallback(series)

        rolling_stds = rolling_std(series, self._spec)
        mean_ = rolling_means.values()[-1]
        std_ = rolling_stds.values()[-1]
        lower, upper = self._band(mean_, std_)
        return Baseline(
            model_code=self.meta.code,
            mean=mean_,
            std=std_,
            lower=lower,
            upper=upper,
            spec=self._spec,
        )

    def _whole_series_fallback(self, series: TimeSeries) -> Baseline:
        values = series.values()
        mean_ = _mean(values)
        std_ = _population_stdev(values, mean=mean_)
        lower, upper = self._band(mean_, std_)
        return Baseline(
            model_code=self.meta.code,
            warnings=(
                "no observation has enough trailing history to satisfy "
                "spec.min_periods; falling back to a whole-series baseline",
            ),
            mean=mean_,
            std=std_,
            lower=lower,
            upper=upper,
            spec=self._spec,
        )

    def _band(self, mean: float, std: float) -> tuple[float, float]:
        return mean - self._k * std, mean + self._k * std
