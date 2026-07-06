"""``mineproductivity.analytics`` -- the platform's statistical and
analytical computation layer, built directly on top of ``kpis``.

Answers the question the KPI Engine deliberately does not: given a
number (or a series of numbers), what does it mean? Analytics consumes
already-correct inputs (raw event rows via ``events.EventStore``, and
already-computed ``kpis.KPIResult`` objects) and produces analytical
judgments about them -- trends, benchmarks, baselines, distributions,
confidence intervals, data-quality scores -- as new, equally
discoverable, equally versioned result objects.

Implements the *Analytics Foundation* portion of
``docs/architecture/06_Analytics_Engine_Design_Specification.md``: the
package's entities, value objects, metadata classes, enums, and
exception hierarchy. Statistical primitives, rolling analytics, trend/
baseline/benchmark computation, data-quality scoring, the pipeline
engine, execution modes, and the plugin registry are later
implementation phases, not yet present in this module -- see the
package's own README.md for status.

``analytics`` depends on ``core``, ``ontology``, ``events``, ``registry``,
``plugins``, ``connectors``, and ``kpis`` -- and MUST NEVER import
``decision``, ``digital_twin``, ``optimization``, ``simulation``,
``agents``, or ``visualization``, none of which this package may see.

Everything documented here is part of the public API and can be
imported directly from ``mineproductivity.analytics``, e.g.::

    from mineproductivity.analytics import AnalyticsModel, TimeSeries
"""

from __future__ import annotations

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.exceptions import (
    AnalyticsModelNotFoundError,
    AnalyticsValidationError,
    AnalyticsVersionConflictError,
    InsufficientDataError,
)
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.result import (
    AnalyticsResult,
    AnomalyFlag,
    Baseline,
    BenchmarkResult,
    ConfidenceInterval,
    DataQualityScore,
    DistributionSummary,
    ForecastResult,
    Histogram,
    OutlierFlag,
    StatisticalSummary,
    TrendResult,
)
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.windowing import RollingSpec

__all__ = [
    "AnalyticsCategory",
    "AnalyticsContext",
    "AnalyticsMetadata",
    "AnalyticsModel",
    "AnalyticsModelNotFoundError",
    "AnalyticsResult",
    "AnalyticsValidationError",
    "AnalyticsVersionConflictError",
    "AnomalyFlag",
    "Baseline",
    "BenchmarkResult",
    "ConfidenceInterval",
    "DataQualityScore",
    "DistributionSummary",
    "ForecastResult",
    "Histogram",
    "InsufficientDataError",
    "OutlierFlag",
    "RollingSpec",
    "StatisticalSummary",
    "TimeSeries",
    "TimeSeriesPoint",
    "TrendResult",
]
