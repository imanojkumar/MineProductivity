"""``DecisionModel``: the "Decision-as-object" root every registrable
decision strategy implements, and ``DecisionContext``, the evidence
bundle a concrete model reasons over.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.events import AsOf, EventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.decision.metadata import DecisionMetadata
from mineproductivity.decision.result import DecisionResult, Recommendation

__all__ = ["DecisionContext", "DecisionModel"]


class DecisionContext:
    """Bundles the collaborators and scope a ``DecisionModel`` needs --
    the decision-layer counterpart to ``analytics.AnalyticsContext``,
    one layer up. Carries the ``KPIResult``/``AnalyticsResult`` evidence
    already gathered, the scope the decision concerns (e.g. a specific
    pit or shift), and optionally an ``EventStore``/``AsOf`` framing a
    point-in-time or hypothetical-scenario view for future root-cause/
    what-if use.

    ``triggered_rules`` is populated by :class:`~mineproductivity.decision.rules.RuleEngineStage`
    (design spec §10) as a pipeline runs, so a downstream
    :class:`~mineproductivity.decision.strategy.ThresholdDecisionStrategy`
    never has to re-run rule evaluation itself -- a necessary, minimal,
    disclosed extension of this class beyond design spec §8's own
    pseudocode (which shows no such field), added in Phase 07.2 because
    §10's ``RuleEngineStage`` explicitly needs *some* way to pass its
    result to the next stage, and this class is the only vehicle a
    ``PipelineStage.process`` has for doing so. Defaults to ``None``,
    meaning "no ``RuleEngineStage`` has run yet" -- deliberately
    **not** ``()``, which is instead the legitimate, common result of a
    ``RuleEngineStage`` that ran and found nothing triggered. Collapsing
    both into the same falsy default would make "not yet computed" and
    "computed as empty" indistinguishable to a downstream consumer
    (caught and fixed during this phase's own QA review, before it
    could silently defeat the "never re-run" guarantee for precisely
    the most common case).

    ``recommendations`` is a Phase 07.3 extension of the same shape and
    for the same reason as ``triggered_rules``: design spec §16's
    ``WeightedScoreRanking`` and §17's ``ExplanationStage`` are, per
    their own pseudocode, ``DecisionModel``/``PipelineStage``
    implementations that operate over a *batch* of already-produced
    ``Recommendation``\\ s, not over raw ``KPIResult``/``AnalyticsResult``
    evidence -- yet ``_decide``/``process`` receive only a
    ``DecisionContext``, the one vehicle available for a caller (or an
    upstream, non-terminal pipeline stage) to hand a batch across. Also
    defaults to ``None`` for consistency with ``triggered_rules``'s own
    field shape -- though, unlike ``triggered_rules``, no consumer in
    this phase currently branches differently on ``None`` versus ``()``
    (:class:`~mineproductivity.decision.ranking.WeightedScoreRanking`
    and :class:`~mineproductivity.decision.explanation.ExplanationStage`
    both treat "not supplied" and "supplied, empty" identically, via a
    plain falsy check); the distinction is preserved as a matter of
    shape consistency and to leave room for a future consumer that
    *does* need to tell the two apart, not because anything here relies
    on it today.

    Examples
    --------
    >>> ctx = DecisionContext(kpi_results=(), analytics_results=(), scope={"pit": "north"})
    >>> ctx.scope
    {'pit': 'north'}
    >>> ctx.event_store is None
    True
    >>> ctx.triggered_rules is None
    True
    >>> ctx.recommendations is None
    True
    """

    def __init__(
        self,
        *,
        kpi_results: Sequence[KPIResult],
        analytics_results: Sequence[AnalyticsResult],
        scope: Mapping[str, str],
        event_store: EventStore[Any] | None = None,
        as_of: AsOf | None = None,
        triggered_rules: Sequence[str] | None = None,
        recommendations: Sequence[Recommendation] | None = None,
    ) -> None:
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.scope = scope
        self.event_store = event_store
        self.as_of = as_of
        self.triggered_rules = None if triggered_rules is None else tuple(triggered_rules)
        self.recommendations = None if recommendations is None else tuple(recommendations)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, scope={self.scope!r}, "
            f"event_store={self.event_store!r}, as_of={self.as_of!r}, "
            f"triggered_rules={self.triggered_rules!r}, recommendations={self.recommendations!r})"
        )


class DecisionModel(ABC):
    """The root of every registrable decision strategy -- 'Decision-as-
    object,' the direct counterpart of ``kpis.BaseKPI`` and
    ``analytics.AnalyticsModel``, one and two layers down respectively.
    A concrete leaf declares ``meta: ClassVar[DecisionMetadata]`` and
    implements :meth:`_decide`; everything else (input validation, result
    envelope wrapping) is inherited.

    **Thread safety.** Every ``DecisionModel`` subclass MUST be stateless
    across :meth:`decide` calls -- no instance attribute is mutated by
    :meth:`_decide` -- so a single instance is safe to share and invoke
    concurrently from multiple threads.
    """

    meta: ClassVar[DecisionMetadata]

    @abstractmethod
    def _decide(self, context: DecisionContext) -> DecisionResult:
        """Pure function: a ``DecisionContext`` in, one ``DecisionResult``
        out. MUST NOT raise for a legitimately no-recommendation input
        (no policy applies, no threshold breached) -- return a
        ``DecisionResult`` carrying zero recommendations and, optionally,
        a warning, the same "qualify, don't coerce" rule
        ``kpis.BaseKPI``/``analytics.AnalyticsModel`` already establish."""

    def decide(self, context: DecisionContext) -> DecisionResult:
        """Non-overridden orchestration: validates ``context`` carries at
        least one ``KPIResult`` or ``AnalyticsResult`` to reason over,
        then calls :meth:`_decide`."""
        if not context.kpi_results and not context.analytics_results:
            return DecisionResult(
                model_code=self.meta.code,
                warnings=(
                    "no evidence in context: at least one KPIResult or AnalyticsResult required",
                ),
            )
        return self._decide(context)
