"""Outlier detection interface (§19) -- interface only.

``OutlierDetector`` is the contract a future outlier-detection plugin
implements. This module ships no concrete subclass, for the same reason
as ``ForecastingModel`` (§16) and ``AnomalyDetector`` (§18) (ADR-0006's
"Alternatives Rejected" section).

Distinct from ``AnomalyDetector`` in scope, not merely in name: an
outlier is a single observation unusual relative to a *static*
distribution (e.g. via IQR or z-score against ``DistributionSummary``,
§23); an anomaly is a point unusual relative to a *temporal* baseline
(§15). The two interfaces are kept separate because the reference data
they compare against differs structurally (a distribution vs. a rolling
baseline), even though a future implementation could satisfy both. This
is reflected here structurally: ``_detect`` requires an already-computed
``DistributionSummary`` (produced by ``statistics.py``'s ``distribution``
function) as its reference -- unlike ``AnomalyDetector._detect``'s
``baseline``, this parameter is mandatory, not optional, exactly
matching design spec §19's own signature (a static distribution is
always the comparison point for an outlier; there is no "compute your
own" fallback the way a temporal baseline can be recomputed internally).

No new result type is introduced: ``OutlierFlag`` already exists in
``result.py`` (Foundation phase) as a plain ``BaseValueObject`` -- not an
``AnalyticsResult`` subclass, for the same reason as ``AnomalyFlag``
(§30's explicit distinction): it represents one flagged observation
within a series, not a summary result about the series as a whole.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.result import DistributionSummary, OutlierFlag
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["OutlierDetector"]


class OutlierDetector(AnalyticsModel, ABC):
    """Contract for a future outlier-detection plugin -- distinct from
    ``AnomalyDetector`` (§18) in scope: an outlier is a single
    observation unusual relative to a static distribution (e.g. via IQR
    or z-score against ``DistributionSummary``, §23); an anomaly is a
    point unusual relative to a *temporal* baseline (§15). The two
    interfaces are kept separate because the reference data they compare
    against differs structurally (a distribution vs. a rolling
    baseline), even though a future implementation could satisfy both.
    THIS MODULE SHIPS NO CONCRETE SUBCLASS, for the same reason as
    ``ForecastingModel``/``AnomalyDetector``.

    Leaves :meth:`~mineproductivity.analytics.abstractions.AnalyticsModel._analyze`
    abstract (inherited, unoverridden) exactly as every other category
    base in this package does (``TrendModel``, ``BaselineModel``,
    ``BenchmarkModel``, ``ForecastingModel``, ``AnomalyDetector``) --
    only a concrete subclass decides how its own ``_analyze`` relates to
    ``_detect``, since no concrete subclass ships here to make that
    decision on a future plugin's behalf.
    """

    @abstractmethod
    def _detect(
        self, series: TimeSeries, *, distribution: DistributionSummary, context: AnalyticsContext
    ) -> Sequence[OutlierFlag]:
        """Flag observations in ``series`` unusual relative to
        ``distribution`` (§23) -- a *static* reference, distinct from
        ``AnomalyDetector`` (§18), which compares against a *temporal*
        baseline instead. ``distribution`` is mandatory: unlike a
        temporal baseline, a static distribution has no "compute your
        own" fallback a detector could reasonably default to."""
