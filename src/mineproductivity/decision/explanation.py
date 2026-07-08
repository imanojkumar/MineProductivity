"""Recommendation explanations (design spec §17).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``ExplanationBuilder`` walks a ``Recommendation``'s own already-carried
``triggered_rules``/``evidence`` fields plus ``DecisionContext``'s own
``kpi_results``/``analytics_results`` -- no new evidence-gathering
mechanism is introduced; every fact cited in a built ``Explanation``
traces back to a value this package already produced elsewhere (§3.2).

Design spec §17's own pseudocode for ``ExplanationStage.process`` is
typed ``(self, context: DecisionContext) -> DecisionContext`` -- a
non-terminal stage -- while its docstring separately describes it as
running "as [a DecisionPipeline's] terminal stage" and "wrap[ping] the
fully-explained set into the final DecisionResult." These two
statements are mutually inconsistent (a stage cannot return
``DecisionContext`` and also be the one that produces the pipeline's
final ``DecisionResult`` -- ``DecisionPipeline.run()``, already locked
since Phase 07.1, requires the terminal stage to yield a
``DecisionResult``). Resolved, as in Phase 07.2's equivalent tensions,
by treating the literal, typed method signature as authoritative:
``ExplanationStage`` is implemented here as a genuinely non-terminal
stage that attaches an ``Explanation`` to every ``Recommendation`` in
``context.recommendations`` and writes the updated batch back, mirroring
``rules.RuleEngineStage``'s own established in-place-mutation pattern
exactly. A caller who wants a single, final, explained
``DecisionResult`` composes ``ExplanationStage`` *before* a genuinely
terminal ``ModelStage`` in the same pipeline (see this module's own
tests for a worked, passing example) -- consistent with, not a
workaround for, the already-locked ``DecisionPipeline`` mechanics.
"""

from __future__ import annotations

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.pipeline import PipelineStage
from mineproductivity.decision.result import Explanation, Recommendation

__all__ = ["ExplanationBuilder", "ExplanationStage"]


class ExplanationBuilder:
    """Walks a ``Recommendation``'s ``triggered_rules``/``evidence`` and
    produces its ``Explanation``. A concrete, non-pluggable utility --
    not a ``DecisionModel`` subclass, since explanation construction is
    not a decision in itself.

    Examples
    --------
    >>> from mineproductivity.kpis import KPIResult
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="x", severity="high", evidence=("UTIL.OEE",),
    ... )
    >>> context = DecisionContext(
    ...     kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
    ...     analytics_results=(), scope={},
    ... )
    >>> explanation = ExplanationBuilder().build(rec, context=context)
    >>> explanation.evidence_refs
    ('UTIL.OEE',)
    >>> len(explanation.premises)
    2
    """

    def build(self, recommendation: Recommendation, *, context: DecisionContext) -> Explanation:
        premises = [
            f"Rule {name!r} triggered under policy {recommendation.policy_code!r}"
            for name in recommendation.triggered_rules
        ]
        for kpi_result in context.kpi_results:
            if kpi_result.code in recommendation.evidence:
                premises.append(f"{kpi_result.code} = {kpi_result.value!r}")
        for analytics_result in context.analytics_results:
            if analytics_result.model_code in recommendation.evidence:
                premises.append(f"{analytics_result.model_code} observed")
        return Explanation(premises=tuple(premises), evidence_refs=recommendation.evidence)


class ExplanationStage(PipelineStage):
    """The ``PipelineStage`` wrapper composing ``ExplanationBuilder``
    into a ``DecisionPipeline`` -- attaches an ``Explanation`` to every
    ``Recommendation`` in ``context.recommendations``, in place (see
    this module's own docstring for why this is non-terminal, matching
    §17's own typed signature).

    Examples
    --------
    >>> from mineproductivity.kpis import KPIResult
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="x", severity="high", evidence=("UTIL.OEE",),
    ... )
    >>> context = DecisionContext(
    ...     kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
    ...     analytics_results=(), scope={}, recommendations=(rec,),
    ... )
    >>> result = ExplanationStage().process(context)
    >>> result.recommendations[0].explanation is not None
    True
    """

    def __init__(self, *, builder: ExplanationBuilder | None = None) -> None:
        self._builder = builder or ExplanationBuilder()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(builder={self._builder!r})"

    def process(self, context: DecisionContext) -> DecisionContext:
        if context.recommendations:
            context.recommendations = tuple(
                recommendation.replace(
                    explanation=self._builder.build(recommendation, context=context)
                )
                for recommendation in context.recommendations
            )
        return context
