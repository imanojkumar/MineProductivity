"""``DecisionPipeline``: composes ordered ``PipelineStage``\\ s over one
``DecisionContext`` into one auditable, reusable decision-evaluation
unit -- the decision-layer equivalent of ``analytics.AnalyticsPipeline``,
one layer up.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from mineproductivity.core import Result

from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.exceptions import DecisionValidationError
from mineproductivity.decision.result import DecisionResult

__all__ = ["DecisionPipeline", "ModelStage", "PipelineStage"]


class PipelineStage(ABC):
    """One step in a ``DecisionPipeline``. Stateless and composable -- a
    new stage never requires changing ``DecisionPipeline`` itself.

    Return type is deliberately ``DecisionContext | DecisionResult``, not
    just ``DecisionContext``: :class:`ModelStage` -- itself a
    ``PipelineStage`` -- always yields a ``DecisionResult``, so the
    honest contract every implementation (terminal or not) must satisfy
    is the union of both. This mirrors
    ``analytics.pipeline.PipelineStage``'s identical, already-disclosed
    widening of its own design spec's abstract-method signature.
    """

    @abstractmethod
    def process(self, context: DecisionContext) -> DecisionContext | DecisionResult:
        """Transform one ``DecisionContext`` into another (e.g.
        attaching rule-evaluation results) -- OR, for a terminal stage,
        wrap the context into a ``DecisionResult`` (see
        :class:`ModelStage`)."""


class ModelStage(PipelineStage):
    """A terminal stage that hands the (by now rule-evaluated) context to
    one ``DecisionModel`` and yields its ``DecisionResult``.

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
    >>> class _Model(DecisionModel):
    ...     meta: ClassVar[DecisionMetadata] = DecisionMetadata(
    ...         code="STRATEGY.Doctest", category=DecisionCategory.STRATEGY, description="x",
    ...     )
    ...     def _decide(self, context):
    ...         return DecisionResult(model_code="TEST")
    >>> stage = ModelStage(_Model())
    >>> from mineproductivity.kpis import KPIResult
    >>> ctx = DecisionContext(kpi_results=(KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),),
    ...                        analytics_results=(), scope={})
    >>> stage.process(ctx).model_code
    'TEST'
    """

    def __init__(self, model: DecisionModel) -> None:
        self._model = model

    def process(self, context: DecisionContext) -> DecisionResult:
        return self._model.decide(context)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(model={self._model!r})"


class DecisionPipeline:
    """An ordered ``Sequence[PipelineStage]``, run in order over one input
    ``DecisionContext`` -- a typical pipeline gathers evidence, evaluates
    rules against an active ``Policy``, generates recommendations, ranks
    them, and explains them.

    A pipeline never contains strategy-specific branching (mirroring
    ``AnalyticsPipeline``'s "holds no model logic" invariant one layer
    down): :meth:`run` calls each stage's :meth:`~PipelineStage.process`
    uniformly and has no knowledge of which concrete ``DecisionModel`` a
    ``ModelStage`` wraps.

    Examples
    --------
    >>> from typing import ClassVar
    >>> from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
    >>> class _Model(DecisionModel):
    ...     meta: ClassVar[DecisionMetadata] = DecisionMetadata(
    ...         code="STRATEGY.Doctest", category=DecisionCategory.STRATEGY, description="x",
    ...     )
    ...     def _decide(self, context):
    ...         return DecisionResult(model_code="TEST")
    >>> from mineproductivity.kpis import KPIResult
    >>> ctx = DecisionContext(kpi_results=(KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),),
    ...                        analytics_results=(), scope={})
    >>> pipeline = DecisionPipeline(stages=(ModelStage(_Model()),))
    >>> pipeline.run(ctx).unwrap().model_code
    'TEST'
    >>> DecisionPipeline(stages=()).run(ctx).is_err
    True
    """

    def __init__(self, stages: Sequence[PipelineStage]) -> None:
        self._stages = tuple(stages)

    def run(self, context: DecisionContext) -> Result[DecisionResult]:
        """Runs every stage in order; a non-terminal stage's output feeds
        the next stage's input. The last stage MUST be a ``ModelStage``
        (or otherwise yield a ``DecisionResult``) or this returns
        ``Result.err(DecisionValidationError(...))``."""
        current: DecisionContext | DecisionResult = context
        for stage in self._stages:
            if isinstance(current, DecisionResult):
                return Result.err(
                    DecisionValidationError(
                        "DecisionPipeline received a DecisionResult from a non-terminal "
                        "stage -- only the pipeline's last stage may yield one"
                    )
                )
            current = stage.process(current)
        if not isinstance(current, DecisionResult):
            return Result.err(
                DecisionValidationError("DecisionPipeline's last stage must yield a DecisionResult")
            )
        return Result.ok(current)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(stages={self._stages!r})"
