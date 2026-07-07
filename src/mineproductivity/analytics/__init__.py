"""``mineproductivity.analytics`` -- the platform's statistical and
analytical computation layer, built directly on top of ``kpis``.

Answers the question the KPI Engine deliberately does not: given a
number (or a series of numbers), what does it mean? Analytics consumes
already-correct inputs (raw event rows via ``events.EventStore``, and
already-computed ``kpis.KPIResult`` objects) and produces analytical
judgments about them -- trends, benchmarks, baselines, distributions,
confidence intervals, data-quality scores -- as new, equally
discoverable, equally versioned result objects.

Implements the *Analytics Foundation* (entities, value objects, metadata
classes, enums, exception hierarchy), the *Metric Pipelines &
Aggregation*, and the *Statistical Primitives* portions of
``docs/architecture/06_Analytics_Engine_Design_Specification.md``:
``AnalyticsPipeline``/``PipelineStage``/``ModelStage`` compose ordered
stages over a ``TimeSeries``; ``AggregationEngine`` group-and-reduces
``kpis.KPIResult`` series, correctly delegating back to
``kpis.KPIEngine`` wherever ``KPIMetadata.aggregation`` requires it
rather than averaging already-computed values; ``describe``,
``percentile``, ``histogram``, ``distribution``, and
``confidence_interval`` are the stateless, deterministic statistical
primitives every concrete ``AnalyticsModel`` calls internally, requiring
no third-party numerical dependency; ``rolling_mean``/``rolling_std``/
``rolling_apply`` are the sliding-window counterparts, reusing
``statistics.py``'s own mean/standard-deviation computation rather than
duplicating it, and representing "not yet enough data" as an absent
point rather than a sentinel value; ``TrendModel``/``LinearTrendModel``
fit a deterministic ordinary-least-squares line over a ``TimeSeries``,
reusing ``statistics.py``'s own mean computation, and characterize the
observed window only -- never extrapolating beyond it (that is
forecasting, a separate, interface-only concern); ``BaselineModel``/
``RollingBaselineModel`` compute a trailing-window ``[mean - k*std,
mean + k*std]`` historical-norm band, consuming ``rolling_mean``/
``rolling_std`` directly rather than reimplementing moving-average
logic; ``BenchmarkModel``/``BandBenchmarkModel`` classify a
``kpis.KPIResult``'s value against its own ``KPIMetadata.benchmark_bands``,
read via ``Registry.metadata_for`` -- never a second, parallel band
schema -- respecting ``KPIMetadata.direction`` (inverting the comparison
for ``LOWER_IS_BETTER``, comparing distance-from-target for
``TARGET_IS_BEST``); ``DataQualityScorer``/``MissingDataPolicy``/
``DataQualityStage`` grade a set of rows against required columns into a
``completeness``/``validity``/``overall_score`` triple and compose
directly into an ``AnalyticsPipeline`` as a ``PipelineStage`` that gates
the pipeline below a caller-configurable minimum score; ``ForecastingModel``
is an interface-only contract (``_forecast(series, *, horizon, context)
-> ForecastResult``) -- this package ships zero concrete subclasses of
it, deliberately: choosing a forecasting algorithm is a modeling
decision outside this package's charter (ADR-0006), left for a future,
independently-versioned plugin to implement against this stable
interface; ``AnomalyDetector`` is likewise an interface-only contract
(``_detect(series, *, baseline, context) -> Sequence[AnomalyFlag]``)
built to be composed with the primitives this package already ships
(``describe``, ``Baseline``, ``rolling_std``) rather than a new
statistical foundation -- this package ships zero concrete subclasses of
it either, for the same ADR-0006 reasoning as ``ForecastingModel``;
``OutlierDetector`` completes the set of three interface-only contracts
(``_detect(series, *, distribution, context) -> Sequence[OutlierFlag]``)
-- distinct from ``AnomalyDetector`` in scope (a *static*
``DistributionSummary`` reference, mandatory, vs. a *temporal*
``Baseline`` reference, optional), ships zero concrete subclasses for
the same reason. The three execution modes (§27-§29) are also
implemented: ``BatchAnalyticsRunner`` is a thin, named wrapper over
``AnalyticsPipeline.run`` for the bounded, retrospective-report mode;
``StreamingAnalyticsSession`` subscribes to an ``events.EventBus`` and
incrementally updates one or more ``IncrementalAccumulator``\\ s as new
envelopes arrive, without ever re-scanning the full ``EventStore``, one
``threading.Lock`` per accumulator key serializing concurrent updates
to that key; ``IncrementalAccumulator`` implements Welford's
online algorithm for O(1)-update, O(1)-memory streaming mean/variance --
the one genuinely new numerical primitive in this package, since
``statistics.py``'s batch functions all require a materialized
``Sequence[float]`` and would defeat the whole point of a streaming
accumulator if reused here instead. ``REGISTRY``/``register`` (§32-33)
specialize ``registry.Registry`` exactly as ``kpis._registry`` does one
layer down; ``LinearTrendModel``, ``RollingBaselineModel``, and
``BandBenchmarkModel`` are all ``@register``-decorated and discoverable
via ``REGISTRY`` at import time. ``AggregationEngine.reduce()`` is fully
implemented: it groups a plain numeric ``TimeSeries`` by scope field(s)
and reuses ``describe()`` verbatim per group, since
``describe()``'s own ``_DEFAULT_PERCENTILES`` guarantees a ``50th``
percentile (median) is always present, resolving the gap that
previously deferred this method (see its own docstring for the full
explanation). Every module described in
``docs/architecture/06_Analytics_Engine_Design_Specification.md`` §6 is
now implemented; see the package's own README.md for the full slice
inventory.

``analytics`` depends on ``core``, ``ontology``, ``events``, ``registry``,
``plugins``, ``connectors``, and ``kpis`` -- and MUST NEVER import
``decision``, ``digital_twin``, ``optimization``, ``simulation``,
``agents``, or ``visualization``, none of which this package may see.

Everything documented here is part of the public API and can be
imported directly from ``mineproductivity.analytics``, e.g.::

    from mineproductivity.analytics import AnalyticsModel, TimeSeries
"""

from __future__ import annotations

from mineproductivity.analytics._registry import REGISTRY, register
from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.aggregation import AggregationEngine, GroupBySpec
from mineproductivity.analytics.anomaly import AnomalyDetector
from mineproductivity.analytics.baseline import BaselineModel, RollingBaselineModel
from mineproductivity.analytics.batch import BatchAnalyticsRunner
from mineproductivity.analytics.benchmarking import BandBenchmarkModel, BenchmarkModel
from mineproductivity.analytics.exceptions import (
    AnalyticsModelNotFoundError,
    AnalyticsValidationError,
    AnalyticsVersionConflictError,
    InsufficientDataError,
)
from mineproductivity.analytics.forecasting import ForecastingModel
from mineproductivity.analytics.incremental import IncrementalAccumulator
from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
from mineproductivity.analytics.outliers import OutlierDetector
from mineproductivity.analytics.pipeline import AnalyticsPipeline, ModelStage, PipelineStage
from mineproductivity.analytics.quality import (
    DataQualityScorer,
    DataQualityStage,
    MissingDataPolicy,
)
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
from mineproductivity.analytics.rolling import rolling_apply, rolling_mean, rolling_std
from mineproductivity.analytics.statistics import (
    confidence_interval,
    describe,
    distribution,
    histogram,
    percentile,
)
from mineproductivity.analytics.streaming import StreamingAnalyticsSession
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint
from mineproductivity.analytics.trend import LinearTrendModel, TrendModel
from mineproductivity.analytics.windowing import RollingSpec

__all__ = [
    "AggregationEngine",
    "AnalyticsCategory",
    "AnalyticsContext",
    "AnalyticsMetadata",
    "AnalyticsModel",
    "AnalyticsModelNotFoundError",
    "AnalyticsPipeline",
    "AnalyticsResult",
    "AnalyticsValidationError",
    "AnalyticsVersionConflictError",
    "AnomalyDetector",
    "AnomalyFlag",
    "BandBenchmarkModel",
    "Baseline",
    "BaselineModel",
    "BatchAnalyticsRunner",
    "BenchmarkModel",
    "BenchmarkResult",
    "ConfidenceInterval",
    "DataQualityScore",
    "DataQualityScorer",
    "DataQualityStage",
    "DistributionSummary",
    "ForecastResult",
    "ForecastingModel",
    "GroupBySpec",
    "Histogram",
    "IncrementalAccumulator",
    "InsufficientDataError",
    "LinearTrendModel",
    "MissingDataPolicy",
    "ModelStage",
    "OutlierDetector",
    "OutlierFlag",
    "PipelineStage",
    "REGISTRY",
    "RollingBaselineModel",
    "RollingSpec",
    "StatisticalSummary",
    "StreamingAnalyticsSession",
    "TimeSeries",
    "TimeSeriesPoint",
    "TrendModel",
    "TrendResult",
    "confidence_interval",
    "describe",
    "distribution",
    "histogram",
    "percentile",
    "register",
    "rolling_apply",
    "rolling_mean",
    "rolling_std",
]
