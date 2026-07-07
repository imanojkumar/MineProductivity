"""``AnalyticsPipeline``: composes ordered ``PipelineStage``\\ s over one
``TimeSeries`` into one auditable, reusable analytical unit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mineproductivity.core import Result

from mineproductivity.analytics.abstractions import AnalyticsContext, AnalyticsModel
from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import AnalyticsResult
from mineproductivity.analytics.timeseries import TimeSeries

__all__ = ["AnalyticsPipeline", "ModelStage", "PipelineStage"]


class PipelineStage(ABC):
    """One step in an ``AnalyticsPipeline``. Stateless and composable --
    a new stage never requires changing ``AnalyticsPipeline`` itself.

    Return type is deliberately ``TimeSeries | AnalyticsResult``, not
    just ``TimeSeries``: :class:`ModelStage` -- itself a ``PipelineStage``
    -- always yields an ``AnalyticsResult``, so the honest contract every
    implementation (terminal or not) must satisfy is the union of both.
    This widens, rather than contradicts, the design spec's own
    abstract-method signature, which showed only ``TimeSeries`` while
    describing ``ModelStage`` as yielding an ``AnalyticsResult`` in the
    very next paragraph -- a necessary, minimal, disclosed correction.
    """

    @abstractmethod
    def process(
        self, series: TimeSeries, *, context: AnalyticsContext
    ) -> TimeSeries | AnalyticsResult:
        """Transform one ``TimeSeries`` into another (e.g. missing-data
        handling, aggregation) -- OR, for a terminal stage, wrap the
        series into an ``AnalyticsResult`` (see :class:`ModelStage`)."""


class ModelStage(PipelineStage):
    """A terminal stage that hands the (by now cleaned/aggregated)
    series to one ``AnalyticsModel`` and yields its ``AnalyticsResult``.

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
    >>> class _FakeStore: ...
    >>> class _Model(AnalyticsModel):
    ...     meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
    ...         code="TREND.Doctest", category=AnalyticsCategory.TREND,
    ...         description="x", min_observations=0,
    ...     )
    ...     def _analyze(self, series, *, context):
    ...         return AnalyticsResult(model_code="TEST")
    >>> stage = ModelStage(_Model())
    >>> ctx = AnalyticsContext(event_store=_FakeStore())
    >>> series = TimeSeries(points=())
    >>> stage.process(series, context=ctx).model_code
    'TEST'
    """

    def __init__(self, model: AnalyticsModel) -> None:
        self._model = model

    def process(self, series: TimeSeries, *, context: AnalyticsContext) -> AnalyticsResult:
        return self._model.analyze(series, context=context)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(model={self._model!r})"


class AnalyticsPipeline:
    """An ordered ``Sequence[PipelineStage]``, run in order over one input
    ``TimeSeries``. Mirrors the shape of the KPI Cookbook's "Putting
    Everything Together" narrative -- fetch, clean, aggregate, analyze --
    generalized to any analytical question.

    A pipeline never contains model-specific branching (mirroring
    ``KPIEngine``'s own "holds no metric logic" invariant one layer up):
    :meth:`run` calls each stage's :meth:`~PipelineStage.process`
    uniformly and has no knowledge of which concrete ``AnalyticsModel`` a
    ``ModelStage`` wraps.

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.analytics.metadata import AnalyticsCategory, AnalyticsMetadata
    >>> class _FakeStore: ...
    >>> class _Model(AnalyticsModel):
    ...     meta: ClassVar[AnalyticsMetadata] = AnalyticsMetadata(
    ...         code="TREND.Doctest", category=AnalyticsCategory.TREND,
    ...         description="x", min_observations=0,
    ...     )
    ...     def _analyze(self, series, *, context):
    ...         return AnalyticsResult(model_code="TEST")
    >>> pipeline = AnalyticsPipeline(stages=(ModelStage(_Model()),))
    >>> ctx = AnalyticsContext(event_store=_FakeStore())
    >>> series = TimeSeries(points=())
    >>> pipeline.run(series, context=ctx).unwrap().model_code
    'TEST'
    >>> AnalyticsPipeline(stages=()).run(series, context=ctx).is_err
    True
    """

    def __init__(self, stages: Sequence[PipelineStage]) -> None:
        self._stages = tuple(stages)

    def run(self, series: TimeSeries, *, context: AnalyticsContext) -> Result[AnalyticsResult]:
        """Runs every stage in order; a non-terminal stage's output feeds
        the next stage's input. The last stage MUST be a ``ModelStage``
        (or otherwise yield an ``AnalyticsResult``) or this returns
        ``Result.err(AnalyticsValidationError(...))``."""
        current: TimeSeries | AnalyticsResult = series
        for stage in self._stages:
            if isinstance(current, AnalyticsResult):
                return Result.err(
                    AnalyticsValidationError(
                        "AnalyticsPipeline received an AnalyticsResult from a non-terminal "
                        "stage -- only the pipeline's last stage may yield one"
                    )
                )
            current = stage.process(current, context=context)
        if not isinstance(current, AnalyticsResult):
            return Result.err(
                AnalyticsValidationError(
                    "AnalyticsPipeline's last stage must yield an AnalyticsResult"
                )
            )
        return Result.ok(current)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(stages={self._stages!r})"
