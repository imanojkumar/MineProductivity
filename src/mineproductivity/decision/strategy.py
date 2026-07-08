"""The pluggable "how do we decide" abstraction (design spec §14), and
the default, concrete, rule/threshold-driven strategy.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``ThresholdDecisionStrategy._decide`` reuses ``rules.RuleEngine.evaluate``
verbatim for rule triggering -- no second rule-evaluation mechanism is
introduced. Threshold-breach comparison reuses the same
comparator-dispatch *shape* ``analytics.benchmarking``'s own
``_COMPARATORS``/``_best_match`` already established (an ``operator``-module
dispatch table keyed by comparator symbol), but is not literally the
same object: ``analytics.benchmarking._COMPARATORS`` is a private,
unexported module constant covering only ``>``/``<``/``>=``/``<=``/``==``
(no ``!=``), one symbol short of :attr:`~mineproductivity.decision.thresholds.Threshold.comparator`'s
full ``Literal['<', '<=', '>', '>=', '==', '!=']`` domain -- reusing it
directly is impossible (it cannot express "!=") without first widening
a different package's private implementation detail, which would be a
worse coupling than a five-line, disclosed duplicate. Field resolution
(``Threshold.field`` against ``DecisionContext`` evidence) is
implemented once, privately, in this module -- design spec §13
explicitly directs that this be "looked up the same straightforward
way ``analytics.DataQualityScorer`` looks up ``required_columns``
against row mappings... not through a bespoke query DSL," which is
followed here: a single ``getattr``-based lookup, no expression parser.
``Recommendation`` construction itself is delegated to
``recommendation.build_recommendation`` -- the module design spec §6
dedicates to generation logic and names among this module's declared
dependencies -- so exactly one summary-text/traceability format exists
package-wide.
"""

from __future__ import annotations

import operator
from abc import ABC
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import ClassVar, Literal

from mineproductivity.decision._registry import register
from mineproductivity.decision.abstractions import DecisionContext, DecisionModel
from mineproductivity.decision.metadata import DecisionCategory, DecisionMetadata
from mineproductivity.decision.policy import Policy
from mineproductivity.decision.recommendation import build_recommendation
from mineproductivity.decision.result import DecisionResult, ThresholdBreach
from mineproductivity.decision.rules import RuleEngine

__all__ = ["DecisionStrategy", "ThresholdDecisionStrategy"]

#: ``Threshold.comparator``'s full domain, unlike
#: ``analytics.benchmarking._COMPARATORS`` (see module docstring for why
#: that one is not reused directly).
_COMPARATORS: Mapping[str, Callable[[float, float], bool]] = {
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


def _resolve_field(context: DecisionContext, field: str) -> float | None:
    """Resolves ``Threshold.field`` against ``context`` evidence (design
    spec §13) -- a plain, dotted-attribute lookup, not a bespoke
    expression language.

    A bare name (no ``.``) is resolved against ``context.kpi_results``:
    the first ``KPIResult`` carrying a numeric attribute of that name
    (typically ``"value"``). A dotted path's first segment selects the
    ``AnalyticsResult`` among ``context.analytics_results`` whose own
    ``model_code`` category prefix (the text before its own first
    ``"."`` -- e.g. ``"trend"`` for ``model_code="TREND.Linear"``,
    matching ``analytics.AnalyticsCategory``'s own member names)
    case-insensitively matches the segment; the remaining path is
    resolved via ``getattr`` from there. Returns ``None`` (never
    raises) when nothing matches -- "qualify, don't coerce": a
    ``Threshold`` referencing evidence this ``DecisionContext`` does
    not carry is legitimately un-evaluable, not an error.
    """
    head, sep, rest = field.partition(".")
    if not sep:
        for kpi_result in context.kpi_results:
            value = getattr(kpi_result, field, None)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        return None
    for analytics_result in context.analytics_results:
        category = analytics_result.model_code.split(".")[0].lower()
        if category == head.lower():
            value = getattr(analytics_result, rest, None)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return None


class DecisionStrategy(DecisionModel, ABC):
    """Category base for decision-making strategies -- the pluggable
    'how do we decide' abstraction, analogous to
    ``analytics.TrendModel``/``BenchmarkModel`` one layer down."""


@register
class ThresholdDecisionStrategy(DecisionStrategy):
    """The default, concrete strategy: evaluate the active ``Policy``'s
    ``Rule``\\ s (via :class:`~mineproductivity.decision.rules.RuleEngine`)
    against the ``DecisionContext``, and produce one ``Recommendation``
    naming every triggered rule.

    Registered into ``decision.REGISTRY`` at import time, mirroring how
    ``analytics.trend``/``analytics.baseline``/``analytics.benchmarking``
    self-register.

    ``severity`` is a constructor parameter, not a ``Policy``/``Threshold``
    field: design spec §12's own ``Policy`` pseudocode (``code``,
    ``version``, ``status``, ``rules``, ``thresholds``, ``strategy_code``)
    and §13's ``Threshold`` pseudocode (``field``, ``comparator``,
    ``limit``) carry no severity-bearing field anywhere, so there is
    nothing to read one from. A constructor parameter models "how bad
    is it when *this* policy's rules fire" as a property of the
    policy/strategy pairing (a reviewed, deliberate choice at
    configuration time), without adding an undocumented field to either
    already-specified, locked value object -- the smallest compatible
    resolution, disclosed here per this phase's own reconciliation rule.

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> from mineproductivity.decision.result import Recommendation
    >>> from mineproductivity.decision.thresholds import Threshold
    >>> from mineproductivity.kpis import KPIResult
    >>> policy = Policy(
    ...     code="AVAIL.LowFleetAvailability",
    ...     rules={"low_oee": PredicateSpecification(
    ...         lambda ctx: any(r.value is not None and r.value < 0.65 for r in ctx.kpi_results)
    ...     )},
    ...     thresholds={"low_oee": Threshold(field="value", comparator="<", limit=0.65)},
    ...     strategy_code="STRATEGY.Threshold",
    ... )
    >>> strategy = ThresholdDecisionStrategy(policy=policy, severity="high")
    >>> context = DecisionContext(
    ...     kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
    ...     analytics_results=(), scope={"pit": "north"},
    ... )
    >>> result = strategy.decide(context)
    >>> isinstance(result, Recommendation)
    True
    >>> result.policy_code, result.triggered_rules, result.severity
    ('AVAIL.LowFleetAvailability', ('low_oee',), 'high')
    >>> strategy.check_thresholds(context)[0].observed_value
    0.58
    """

    meta: ClassVar[DecisionMetadata] = DecisionMetadata(
        code="STRATEGY.Threshold",
        category=DecisionCategory.STRATEGY,
        description="Evaluate a Policy's rules against a DecisionContext, producing "
        "one Recommendation naming every triggered rule.",
    )

    def __init__(
        self,
        *,
        policy: Policy,
        rule_engine: RuleEngine | None = None,
        severity: Literal["low", "medium", "high", "critical"] = "medium",
    ) -> None:
        self._policy = policy
        self._rule_engine = rule_engine or RuleEngine()
        self._severity = severity

    def __repr__(self) -> str:
        return f"{type(self).__name__}(policy={self._policy!r}, severity={self._severity!r})"

    def _decide(self, context: DecisionContext) -> DecisionResult:
        triggered = (
            context.triggered_rules
            if context.triggered_rules is not None
            else tuple(self._rule_engine.evaluate(self._policy.rules, context))
        )
        if not triggered:
            return DecisionResult(model_code=self.meta.code)

        evidence = tuple(result.code for result in context.kpi_results) + tuple(
            result.model_code for result in context.analytics_results
        )
        return build_recommendation(
            policy=self._policy,
            triggered_rules=tuple(triggered),
            evidence=evidence,
            severity=self._severity,
            model_code=self.meta.code,
        )

    def check_thresholds(self, context: DecisionContext) -> tuple[ThresholdBreach, ...]:
        """Independently checks every ``Threshold`` in ``self._policy.thresholds``
        against ``context`` evidence, returning a ``ThresholdBreach`` for
        each one whose comparator/limit the resolved observed value
        satisfies. A ``Threshold`` whose ``field`` cannot be resolved
        against ``context`` (see :func:`_resolve_field`) is silently
        skipped, never raised -- "qualify, don't coerce"."""
        now = datetime.now(timezone.utc)
        breaches: list[ThresholdBreach] = []
        for threshold in self._policy.thresholds.values():
            observed = _resolve_field(context, threshold.field)
            if observed is None:
                continue
            if _COMPARATORS[threshold.comparator](observed, threshold.limit):
                breaches.append(
                    ThresholdBreach(threshold=threshold, observed_value=observed, breached_at=now)
                )
        return tuple(breaches)
