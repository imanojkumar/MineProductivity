"""Batch analytics (§28): the "normal," retrospective-report execution
mode, in contrast to ``streaming.py``'s live, unbounded mode (§27).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
The one thing this module needs -- "run one pipeline once over a
bounded input and produce a single result" -- is exactly what
``AnalyticsPipeline.run()`` (§9) already does. No new orchestration
logic is introduced: ``BatchAnalyticsRunner`` is a thin, named wrapper
that stores the ``pipeline``/``context`` pair and delegates ``run()``
verbatim. It exists as its own class (rather than callers invoking
``AnalyticsPipeline.run`` directly) purely so "batch" and "streaming"
are two clearly-named, symmetrical entry points in the public API (§7),
matching how a reader of this specification's table of contents
(§27-§29) expects to find them -- not because any new behavior is
required.
"""

from __future__ import annotations

from mineproductivity.core import Result

from mineproductivity.analytics.abstractions import AnalyticsContext
from mineproductivity.analytics.pipeline import AnalyticsPipeline
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["BatchAnalyticsRunner"]


class BatchAnalyticsRunner:
    """Runs one ``AnalyticsPipeline`` once over a bounded ``TimeSeries``
    and returns a single ``AnalyticsResult`` -- the 'normal,'
    retrospective-report mode, in contrast to
    ``StreamingAnalyticsSession``'s live, unbounded mode (§27).

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.analytics.abstractions import AnalyticsModel
    >>> from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
    >>> from mineproductivity.analytics.pipeline import ModelStage
    >>> from mineproductivity.events.store import _InMemoryEventStore
    >>> class _Model(AnalyticsModel):
    ...     meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
    ...         code="TREND.Doctest", category=AnalyticsCategory.TREND,
    ...         description="x", min_observations=0,
    ...     )
    ...     def _analyze(self, series, *, context):
    ...         return AnalyticsResult(model_code="TEST")
    >>> pipeline = AnalyticsPipeline(stages=(ModelStage(_Model()),))
    >>> context = AnalyticsContext(event_store=_InMemoryEventStore())
    >>> runner = BatchAnalyticsRunner(pipeline=pipeline, context=context)
    >>> result = runner.run(TimeSeries(points=()))
    >>> result.unwrap().model_code
    'TEST'
    """

    def __init__(self, *, pipeline: AnalyticsPipeline, context: AnalyticsContext) -> None:
        self._pipeline = pipeline
        self._context = context

    def run(self, series: TimeSeries) -> Result[AnalyticsResult]:
        return self._pipeline.run(series, context=self._context)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(pipeline={self._pipeline!r}, context={self._context!r})"
