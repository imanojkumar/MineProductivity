"""``AnalyticsResult``: the shared envelope every concrete Analytics
output composes, and every concrete result dataclass built on it.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Literal

from mineproductivity.core import BaseValueObject
from mineproductivity.kpis import Direction, Window

from mineproductivity.analytics.windowing import RollingSpec

__all__ = [
    "AnalyticsResult",
    "AnomalyFlag",
    "Baseline",
    "BenchmarkResult",
    "ConfidenceInterval",
    "DataQualityScore",
    "DistributionSummary",
    "ForecastResult",
    "Histogram",
    "OutlierFlag",
    "StatisticalSummary",
    "TrendResult",
]


@dataclasses.dataclass(frozen=True, slots=True)
class AnalyticsResult(BaseValueObject):
    """The shared envelope every concrete Analytics result composes.
    Mirrors ``KPIResult``'s role as the one result shape -- except
    Analytics genuinely has more than one *kind* of output, so this is a
    shared base rather than ``kpis``' single concrete type.

    Examples
    --------
    >>> AnalyticsResult(model_code="TREND.Linear").model_code
    'TREND.Linear'
    >>> AnalyticsResult(warnings=("insufficient data",)).warnings
    ('insufficient data',)
    """

    model_code: str = dataclasses.field(default="", kw_only=True)
    computed_at: datetime = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc), kw_only=True
    )
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class StatisticalSummary(AnalyticsResult):
    """Descriptive statistics over a
    :class:`~mineproductivity.analytics.timeseries.TimeSeries` -- the
    Analytics-layer equivalent of a spreadsheet's "Descriptive
    Statistics" tool.

    Examples
    --------
    >>> s = StatisticalSummary(n=3, mean=2.0, std=1.0, minimum=1.0,
    ...                         maximum=3.0, percentiles={50: 2.0})
    >>> s.percentiles[50]
    2.0
    """

    n: int
    mean: float
    std: float
    minimum: float
    maximum: float
    percentiles: Mapping[int, float]

    def _normalize(self) -> None:
        super(StatisticalSummary, self)._normalize()
        object.__setattr__(self, "percentiles", MappingProxyType(dict(self.percentiles)))


@dataclasses.dataclass(frozen=True, slots=True)
class TrendResult(AnalyticsResult):
    """The outcome of a trend-fitting model -- characterizes an observed
    series' direction and fit quality; never a prediction of a future
    value (that is forecasting, a separate concern).

    Examples
    --------
    >>> TrendResult(slope=1.5, intercept=0.0, r_squared=0.98,
    ...              direction="increasing", window=RollingSpec(periods=7)).direction
    'increasing'
    """

    slope: float
    intercept: float
    r_squared: float
    direction: Literal["increasing", "decreasing", "flat"]
    window: Window | RollingSpec


@dataclasses.dataclass(frozen=True, slots=True)
class BenchmarkResult(AnalyticsResult):
    """Classification of a ``KPIResult`` against its own
    ``KPIMetadata.benchmark_bands``/``direction``.

    Examples
    --------
    >>> BenchmarkResult(kpi_code="PROD.TPH", value=1200.0,
    ...                  band="top_quartile", direction=Direction.HIGHER_IS_BETTER).band
    'top_quartile'
    """

    kpi_code: str
    value: float
    band: str
    direction: Direction


@dataclasses.dataclass(frozen=True, slots=True)
class Baseline(AnalyticsResult):
    """A self-referential historical-norm band -- distinct from
    :class:`BenchmarkResult`, which compares against an externally
    published target/band.

    Examples
    --------
    >>> b = Baseline(mean=100.0, std=5.0, lower=90.0, upper=110.0,
    ...               spec=RollingSpec(periods=14))
    >>> b.lower, b.upper
    (90.0, 110.0)
    """

    mean: float
    std: float
    lower: float
    upper: float
    spec: RollingSpec


@dataclasses.dataclass(frozen=True, slots=True)
class DistributionSummary(AnalyticsResult):
    """A superset of :class:`StatisticalSummary` that adds shape
    descriptors (``skewness``, ``kurtosis``) that ``describe()``
    deliberately omits, keeping ``describe()`` cheap.

    Examples
    --------
    >>> d = DistributionSummary(mean=1.0, std=0.5, skewness=0.1,
    ...                          kurtosis=3.0, percentiles={50: 1.0})
    >>> d.skewness
    0.1
    """

    mean: float
    std: float
    skewness: float
    kurtosis: float
    percentiles: Mapping[int, float]

    def _normalize(self) -> None:
        super(DistributionSummary, self)._normalize()
        object.__setattr__(self, "percentiles", MappingProxyType(dict(self.percentiles)))


@dataclasses.dataclass(frozen=True, slots=True)
class Histogram(AnalyticsResult):
    """A binned frequency count over a sequence of values.

    Examples
    --------
    >>> h = Histogram(bin_edges=(0.0, 1.0, 2.0), counts=(3, 5))
    >>> len(h.counts) == len(h.bin_edges) - 1
    True
    """

    bin_edges: tuple[float, ...]
    counts: tuple[int, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class ConfidenceInterval(AnalyticsResult):
    """A closed-form (``normal`` or Student's ``t``) interval around a
    sample mean.

    Examples
    --------
    >>> ci = ConfidenceInterval(lower=9.5, upper=10.5, confidence=0.95, method="t")
    >>> ci.confidence
    0.95
    """

    lower: float
    upper: float
    confidence: float
    method: Literal["normal", "t"]


@dataclasses.dataclass(frozen=True, slots=True)
class DataQualityScore(AnalyticsResult):
    """A graded completeness/validity judgment over a set of rows
    against a set of required columns -- the single number a pipeline
    gates on is ``overall_score``.

    Examples
    --------
    >>> q = DataQualityScore(completeness=1.0, validity=0.9,
    ...                       overall_score=0.9, reasons=("2 rows out of range",))
    >>> q.overall_score
    0.9
    """

    completeness: float
    validity: float
    overall_score: float
    reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class ForecastResult(AnalyticsResult):
    """``horizon`` future points, each with a point estimate and an
    uncertainty band. No producer of this result type ships in this
    release -- :class:`~mineproductivity.analytics.abstractions.AnalyticsModel`
    subclasses that produce it are a future forecasting plugin's job.

    Examples
    --------
    >>> f = ForecastResult(horizon=1, predicted=(105.0,),
    ...                     intervals=(ConfidenceInterval(lower=100.0, upper=110.0,
    ...                                                    confidence=0.95, method="normal"),))
    >>> f.horizon
    1
    """

    horizon: int
    predicted: tuple[float, ...]
    intervals: tuple[ConfidenceInterval, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class AnomalyFlag(BaseValueObject):
    """One flagged *observation within* a series -- deliberately a plain
    ``BaseValueObject``, not an :class:`AnalyticsResult` subclass, since
    it represents one point, not a summary result about a series.

    Examples
    --------
    >>> AnomalyFlag(timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ...              observed_value=500.0, expected_value=100.0, severity="high").severity
    'high'
    """

    timestamp: datetime
    observed_value: float
    expected_value: float | None
    severity: Literal["low", "medium", "high"]


@dataclasses.dataclass(frozen=True, slots=True)
class OutlierFlag(BaseValueObject):
    """One observation unusual relative to a static distribution --
    deliberately a plain ``BaseValueObject``, not an
    :class:`AnalyticsResult` subclass, for the same reason as
    :class:`AnomalyFlag`.

    Examples
    --------
    >>> OutlierFlag(index=42, value=999.0, method_hint="iqr").method_hint
    'iqr'
    """

    index: int
    value: float
    method_hint: str
