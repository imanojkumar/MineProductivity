"""Anomaly detection interface (§18) -- interface only.

``AnomalyDetector`` is the contract a future anomaly-detection plugin
implements. This module ships no concrete subclass, for the same reason
as ``ForecastingModel`` (§16): "is this point anomalous" is a modeling
choice (z-score threshold? seasonal decomposition? isolation-forest-style
ensembling?) this package does not make on the implementer's behalf
(ADR-0006's "Alternatives Rejected" section). A future detector is
expected to be built on top of the primitives this package DOES ship
(``describe``, ``Baseline``, ``rolling_std``), not on a new statistical
foundation -- reflected here structurally: ``_detect`` accepts an
already-computed ``Baseline`` (produced by ``baseline.py``'s
``RollingBaselineModel``) as its reference, rather than this interface
recomputing one itself.

No new result type is introduced: ``AnomalyFlag`` already exists in
``result.py`` (Foundation phase) as a plain ``BaseValueObject`` -- not an
``AnalyticsResult`` subclass, since it represents one flagged
observation within a series, not a summary result about the series as a
whole (§30's explicit distinction).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.result import AnomalyFlag, Baseline
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["AnomalyDetector"]


class AnomalyDetector(AnalyticsModel, ABC):
    """Contract for a future anomaly-detection plugin. THIS MODULE SHIPS
    NO CONCRETE SUBCLASS, for the same reason as ``ForecastingModel``
    (§16): "is this point anomalous" is a modeling choice this package
    does not make on the implementer's behalf. A future detector is
    expected to be built on top of the primitives this package DOES ship
    (``describe``, ``Baseline``, ``rolling_std``), not on a new
    statistical foundation.

    Leaves :meth:`~mineproductivity.analytics.abstractions.AnalyticsModel._analyze`
    abstract (inherited, unoverridden) exactly as every other category
    base in this package does (``TrendModel``, ``BaselineModel``,
    ``BenchmarkModel``, ``ForecastingModel``) -- only a concrete
    subclass decides how its own ``_analyze`` relates to ``_detect``,
    since no concrete subclass ships here to make that decision on a
    future plugin's behalf.
    """

    @abstractmethod
    def _detect(
        self, series: TimeSeries, *, baseline: Baseline | None, context: AnalyticsContext
    ) -> Sequence[AnomalyFlag]:
        """Flag observations in ``series`` unusual relative to
        ``baseline`` (§15) -- a *temporal* reference, distinct from
        ``OutlierDetector`` (§19), which compares against a *static*
        distribution instead. ``baseline`` is optional: a future
        detector may compute its own reference internally rather than
        requiring a pre-computed one."""
