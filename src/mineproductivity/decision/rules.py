"""Rule evaluation (design spec §10, §11) via composition, not a bespoke
rule language.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseSpecification`` (and its ``&``/``|``/``~``-composable
``AndSpecification``/``OrSpecification``/``NotSpecification``/
``PredicateSpecification`` family) is reused verbatim as ``Rule``'s
underlying shape -- exactly the pattern ``events.EventFilter = BaseSpecification[EventEnvelope[Any]]``
already established (spec 01) and that this package's own design spec
explicitly directs (§10: "no bespoke rule language is introduced
anywhere in this package"). No new composition operator, boolean
expression parser, or predicate abstraction is introduced. Rule
isolation (one malformed rule's exception must not prevent the rest
from being evaluated) mirrors ``registry.EntryPointDiscovery``'s own
per-entry-point isolation guarantee (spec 03 §11), applied here to rule
predicates instead of plugin imports -- the same try/except-around-one-
item, continue-on-failure shape, not a new isolation mechanism.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from mineproductivity.core import BaseSpecification

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.pipeline import PipelineStage

if TYPE_CHECKING:
    # Deferred to avoid a runtime circular import: policy.py imports Rule
    # from this module (Policy.rules: Mapping[str, Rule]), so this module
    # cannot import Policy at runtime. `from __future__ import annotations`
    # already makes every annotation in this file a lazy string, so a
    # TYPE_CHECKING-only import is sufficient for mypy without ever being
    # evaluated at import time.
    from mineproductivity.decision.policy import Policy

__all__ = ["Rule", "RuleEngine", "RuleEngineStage"]

_logger = logging.getLogger(__name__)

type Rule = BaseSpecification[DecisionContext]
"""Reuses ``core.BaseSpecification`` (``&``/``|``/``~`` composable)
exactly as ``events.EventFilter`` already does -- rule evaluation is
never a bespoke DSL in this platform."""


class RuleEngine:
    """Evaluates a named mapping of :data:`Rule`\\ s against one
    ``DecisionContext``, isolating one rule's evaluation failure from
    the rest.

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> from mineproductivity.kpis import KPIResult
    >>> low_oee: Rule = PredicateSpecification(
    ...     lambda ctx: any(r.value is not None and r.value < 0.65 for r in ctx.kpi_results)
    ... )
    >>> context = DecisionContext(
    ...     kpi_results=(KPIResult(code="UTIL.OEE", value=0.58, unit=""),),
    ...     analytics_results=(), scope={},
    ... )
    >>> RuleEngine().evaluate({"low_oee": low_oee}, context)
    ('low_oee',)
    """

    def evaluate(self, rules: Mapping[str, Rule], context: DecisionContext) -> Sequence[str]:
        """Returns the names of every rule satisfied by ``context``, in a
        stable (sorted) order. A single rule raising during
        ``is_satisfied_by`` is caught, logged, and excluded from the
        result -- never allowed to prevent evaluation of the remaining
        rules."""
        triggered: list[str] = []
        for name in sorted(rules):
            try:
                if rules[name].is_satisfied_by(context):
                    triggered.append(name)
            except Exception:
                _logger.warning("rule %r raised during evaluation; excluded from result", name)
                continue
        return tuple(triggered)


class RuleEngineStage(PipelineStage):
    """The ``PipelineStage`` wrapper composing ``RuleEngine`` into a
    ``DecisionPipeline`` -- attaches the triggered rule names to the
    ``DecisionContext`` passed downstream, so
    ``ModelStage(ThresholdDecisionStrategy(policy=policy))`` never has
    to re-run rule evaluation itself.

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> from mineproductivity.decision.policy import Policy
    >>> policy = Policy(
    ...     code="TEST.Policy", rules={"always": PredicateSpecification(lambda ctx: True)},
    ...     strategy_code="STRATEGY.Threshold",
    ... )
    >>> stage = RuleEngineStage(policy=policy)
    >>> context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
    >>> stage.process(context).triggered_rules
    ('always',)
    """

    def __init__(self, *, policy: "Policy") -> None:
        self._policy = policy

    def process(self, context: DecisionContext) -> DecisionContext:
        context.triggered_rules = tuple(RuleEngine().evaluate(self._policy.rules, context))
        return context

    def __repr__(self) -> str:
        return f"{type(self).__name__}(policy={self._policy!r})"
