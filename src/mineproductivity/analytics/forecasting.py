"""Forecasting interface (§16) -- interface only.

``ForecastingModel`` is the contract a future forecasting plugin
implements. This module ships no concrete subclass: choosing a
forecasting algorithm (exponential smoothing, ARIMA, or anything else)
is a modeling decision this package deliberately does not make (§3.1,
§3.4) -- the same reasoning ``trend.py`` already states for why
``LinearTrendModel`` characterizes an observed window only and never
extrapolates. Defining the contract now lets a future,
independently-versioned plugin register against a stable interface
without waiting for a future revision of this specification (ADR-0006's
"Alternatives Rejected" section explicitly rejects shipping a concrete
forecasting implementation in this release, on "scope creep into
machine learning" and "premature commitment to an interface's shape via
its first implementation" grounds).

No new result type is introduced: ``ForecastResult`` and
``ConfidenceInterval`` already exist in ``result.py`` (Foundation phase)
-- a forecast is ``horizon`` future points, each a point estimate plus an
uncertainty band, exactly what those two existing types already compose.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.result import ForecastResult
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["ForecastingModel"]


class ForecastingModel(AnalyticsModel, ABC):
    """The contract a future forecasting plugin implements. THIS MODULE
    SHIPS NO CONCRETE SUBCLASS -- choosing a forecasting algorithm is a
    modeling decision this package deliberately does not make (§3.4).
    Defining the contract now lets a future, independently-versioned
    plugin register against a stable interface without waiting for a
    future revision of this specification.

    Leaves :meth:`~mineproductivity.analytics.abstractions.AnalyticsModel._analyze`
    abstract (inherited, unoverridden) exactly as every other category
    base in this package does (``TrendModel``, ``BaselineModel``,
    ``BenchmarkModel``) -- only a concrete subclass decides how its own
    ``_analyze`` relates to ``_forecast``, since no concrete subclass
    ships here to make that decision on a future plugin's behalf.
    """

    @abstractmethod
    def _forecast(
        self, series: TimeSeries, *, horizon: int, context: AnalyticsContext
    ) -> ForecastResult:
        """``horizon`` future points, each with a point estimate and an
        uncertainty band (:class:`~mineproductivity.analytics.result.ConfidenceInterval`,
        §24)."""
