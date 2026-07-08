"""Recommendation ranking (design spec §16) -- a distinct question from
prioritization (§20): ranking answers "which recommendation is best,"
prioritization answers "given limited capacity, which action happens
first" (conflating the two is a recorded anti-pattern, §33).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``WeightedScoreRanking`` reuses ``scoring.DecisionScorer`` verbatim for
the numeric weight backing the sort -- no second scoring mechanism is
introduced. Ordering reuses Python's own stable ``sorted()`` (never a
hand-rolled comparison sort), so recommendations with equal
``DecisionScore.value`` deterministically preserve their input relative
order -- a genuine, disclosed tie-break rule, not an accident of
implementation.

Design spec §16's own pseudocode shows only ``WeightedScoreRanking.__init__``
-- no explicit method for ranking a batch is given. Two things are
therefore genuinely necessary and are disclosed together: (1) a public
``rank()`` method, the natural, directly-testable expression of this
class's own stated responsibility ("orders Recommendations... by
DecisionScore.value, descending"); (2) since ``RankingStrategy``
inherits from ``DecisionModel`` (per the design spec's own class
diagram), ``_decide`` must still be implemented to satisfy that
abstract contract -- built as a thin adapter over ``rank()``, reading
the batch from ``DecisionContext.recommendations`` (see
``abstractions.DecisionContext``'s own docstring for why that field
exists) and returning the top-ranked item as "the decision."
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import ClassVar

from mineproductivity.decision._registry import register
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.result import DecisionResult, RankedRecommendation, Recommendation
from mineproductivity.decision.scoring import DecisionScorer

__all__ = ["RankingStrategy", "WeightedScoreRanking"]


class RankingStrategy(DecisionModel, ABC):
    """Category base for ranking strategies -- orders candidate
    ``Recommendation``\\ s by :class:`~mineproductivity.decision.result.DecisionScore`.
    Distinct from :class:`~mineproductivity.decision.prioritization.ActionPrioritizer`
    (§20): ranking answers "which recommendation is best," prioritization
    answers "given limited capacity, which action happens first" --
    conflating the two is a recorded anti-pattern (§33)."""


@register
class WeightedScoreRanking(RankingStrategy):
    """The default, concrete ranking strategy: orders ``Recommendation``\\ s
    by ``DecisionScore.value``, descending. Ties preserve input relative
    order (Python's ``sorted()`` is stable).

    Registered into ``decision.REGISTRY`` at import time, mirroring how
    ``strategy.ThresholdDecisionStrategy`` self-registers.

    Examples
    --------
    >>> low = Recommendation(
    ...     policy_code="A", triggered_rules=("r",), summary="x", severity="low", evidence=(),
    ... )
    >>> critical = Recommendation(
    ...     policy_code="B", triggered_rules=("r",), summary="x", severity="critical", evidence=(),
    ... )
    >>> ranked = WeightedScoreRanking().rank([low, critical])
    >>> [item.recommendation.policy_code for item in ranked]
    ['B', 'A']
    >>> [item.rank for item in ranked]
    [1, 2]
    """

    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="RANKING.WeightedScore",
        category=DecisionCategory.RANKING,
        description="Order Recommendations by DecisionScore.value, descending.",
    )

    def __init__(self, *, scorer: DecisionScorer | None = None) -> None:
        self._scorer = scorer or DecisionScorer()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(scorer={self._scorer!r})"

    def rank(self, recommendations: Sequence[Recommendation]) -> Sequence[RankedRecommendation]:
        """Scores every ``Recommendation`` via ``DecisionScorer``, then
        orders them by ``DecisionScore.value``, descending, assigning
        each its 1-based ``rank`` position."""
        scored = [
            (recommendation, self._scorer.score(recommendation))
            for recommendation in recommendations
        ]
        scored.sort(key=lambda pair: pair[1].value, reverse=True)
        return tuple(
            RankedRecommendation(
                model_code=self.meta.code, recommendation=recommendation, score=score, rank=index
            )
            for index, (recommendation, score) in enumerate(scored, start=1)
        )

    def _decide(self, context: DecisionContext) -> DecisionResult:
        if not context.recommendations:
            return DecisionResult(
                model_code=self.meta.code, warnings=("no recommendations to rank",)
            )
        return self.rank(context.recommendations)[0]
