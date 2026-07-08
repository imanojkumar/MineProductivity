"""``DecisionResult``: the shared envelope every concrete Decision
output composes, and every concrete result/value type built on it
(design spec §28).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as every type's base, and
the ``MappingProxyType``-freezing convention for ``Mapping``-typed
fields is reused exactly as ``analytics.result``/``analytics.timeseries``
already established -- no new value-object base or mapping-freezing
mechanism is introduced. ``ConfidenceScore`` (§24) is defined here
exactly per the design spec's own §24 code block (``value``, ``basis``
only) -- the design spec's §6 module-dependency table separately notes
result.py depends on "``analytics`` (``DataQualityScore``, referenced by
``ConfidenceScore``)"; read against §24's own precise pseudocode, this
describes how ``scoring.ConfidenceScorer`` (a later phase, out of scope
here) *derives* a ``ConfidenceScore.value`` from
``analytics.DataQualityScore`` at runtime, not a field on this dataclass
-- a minor, disclosed spec-internal imprecision, not acted on literally,
the same kind of judgment call already applied to spec 06 §7's
``ForecastResult`` omission. Consequently this module has zero
dependency on ``mineproductivity.analytics``.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Literal

from mineproductivity.core import BaseValueObject

from mineproductivity.decision.thresholds import Threshold

__all__ = [
    "ActionPlan",
    "ActionPriority",
    "Alert",
    "ConfidenceScore",
    "DecisionResult",
    "DecisionScore",
    "Explanation",
    "RankedRecommendation",
    "Recommendation",
    "RootCauseResult",
    "ThresholdBreach",
    "WhatIfResult",
]


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionResult(BaseValueObject):
    """The shared envelope every concrete Decision output composes --
    mirrors ``analytics.AnalyticsResult``'s role, one layer up.

    Examples
    --------
    >>> DecisionResult(model_code="STRATEGY.Threshold").model_code
    'STRATEGY.Threshold'
    >>> DecisionResult(warnings=("no evidence in context",)).warnings
    ('no evidence in context',)
    """

    model_code: str = dataclasses.field(default="", kw_only=True)
    computed_at: datetime = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc), kw_only=True
    )
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class Explanation(BaseValueObject):
    """A structured, evidence-linked justification -- never opaque prose
    only (design spec §17). ``premises`` are human-readable statements;
    ``evidence_refs`` are the exact ``KPIResult.code``/
    ``AnalyticsResult.model_code`` values a consuming system can re-fetch
    to verify the claim independently.

    Deliberately a plain ``BaseValueObject``, not a ``DecisionResult``
    subclass -- it is a supporting value attached to a decision output,
    not a decision output itself (§28).

    Examples
    --------
    >>> Explanation(premises=("OEE below 0.65",), evidence_refs=("UTIL.OEE",)).premises
    ('OEE below 0.65',)
    """

    premises: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionScore(BaseValueObject):
    """The numeric weight backing ranking (design spec §16, §23).
    ``components`` names the contributing factors, for auditability --
    an operator reviewing a ranked list can see *why* one recommendation
    outranked another, not merely trust the aggregate.

    Examples
    --------
    >>> DecisionScore(value=0.8, components={"severity": 0.5, "policy_weight": 0.3}).value
    0.8
    """

    value: float
    components: Mapping[str, float]

    def _normalize(self) -> None:
        super(DecisionScore, self)._normalize()
        object.__setattr__(self, "components", MappingProxyType(dict(self.components)))


@dataclasses.dataclass(frozen=True, slots=True)
class ConfidenceScore(BaseValueObject):
    """The trust weight backing how strongly a recommendation should be
    acted on (design spec §24). ``basis`` records which evidence path
    produced ``value`` -- ``"data_quality"``/``"rule_strength"``/
    ``"combined"`` -- so a consumer can distinguish "we checked data
    quality and it was good" from "we had no data-quality signal to
    check."

    Examples
    --------
    >>> ConfidenceScore(value=0.9, basis="data_quality").basis
    'data_quality'
    """

    value: float
    basis: Literal["data_quality", "rule_strength", "combined"]


@dataclasses.dataclass(frozen=True, slots=True)
class ActionPriority(BaseValueObject):
    """Urgency/impact/effort under limited execution capacity (design
    spec §20) -- a distinct question from ranking (§16). All three
    components are retained alongside the aggregate ``priority_score``
    so an operator can audit the arithmetic, not merely trust it.

    Examples
    --------
    >>> ActionPriority(urgency=0.8, impact=0.6, effort=0.2).priority_score
    2.4
    """

    urgency: float
    impact: float
    effort: float

    @property
    def priority_score(self) -> float:
        return (self.urgency * self.impact) / max(self.effort, 1e-9)


@dataclasses.dataclass(frozen=True, slots=True)
class ThresholdBreach(BaseValueObject):
    """Records exactly which ``Threshold``, at what observed value, was
    crossed (design spec §13, §28) -- the audit-trail-facing companion
    to ``Threshold`` itself.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> breach = ThresholdBreach(
    ...     threshold=Threshold(field="value", comparator="<", limit=0.65),
    ...     observed_value=0.58,
    ...     breached_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ... )
    >>> breach.observed_value
    0.58
    """

    threshold: Threshold
    observed_value: float
    breached_at: datetime


@dataclasses.dataclass(frozen=True, slots=True)
class Recommendation(DecisionResult):
    """One recommended action, produced by a ``DecisionStrategy`` (design
    spec §15) -- always traceable to the specific ``Policy``/``Rule``
    names that produced it (``policy_code``, ``triggered_rules``) and to
    the specific ``KPIResult``/``AnalyticsResult`` evidence it was
    computed from (``evidence``).

    Examples
    --------
    >>> Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="Investigate fleet availability", severity="high",
    ...     evidence=("UTIL.OEE",),
    ... ).severity
    'high'
    """

    policy_code: str
    triggered_rules: tuple[str, ...]
    summary: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence: tuple[str, ...]
    explanation: Explanation | None = dataclasses.field(default=None, kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class RankedRecommendation(DecisionResult):
    """One ``Recommendation`` ordered into a ranked sequence by
    ``DecisionScore`` (design spec §16).

    Examples
    --------
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="Investigate fleet availability", severity="high", evidence=("UTIL.OEE",),
    ... )
    >>> RankedRecommendation(
    ...     recommendation=rec, score=DecisionScore(value=0.8, components={}), rank=1,
    ... ).rank
    1
    """

    recommendation: Recommendation
    score: DecisionScore
    rank: int


@dataclasses.dataclass(frozen=True, slots=True)
class ActionPlan(DecisionResult):
    """A topologically-ordered sequence of prioritized actions, respecting
    declared dependencies (design spec §21).

    Examples
    --------
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="Investigate fleet availability", severity="high", evidence=("UTIL.OEE",),
    ... )
    >>> plan = ActionPlan(
    ...     ordered_actions=(rec,),
    ...     priorities={"AVAIL.LowFleetAvailability": ActionPriority(urgency=0.8, impact=0.6, effort=0.2)},
    ... )
    >>> len(plan.ordered_actions)
    1
    """

    ordered_actions: tuple[Recommendation, ...]
    priorities: Mapping[str, ActionPriority]

    def _normalize(self) -> None:
        super(ActionPlan, self)._normalize()
        object.__setattr__(self, "priorities", MappingProxyType(dict(self.priorities)))


@dataclasses.dataclass(frozen=True, slots=True)
class Alert(DecisionResult):
    """Produced from a ``ThresholdBreach`` or a high-severity
    ``Recommendation`` (design spec §22). ``AlertGenerator`` (a later
    phase, out of scope here) produces this value object only -- channel
    delivery is explicitly out of this package's scope.

    Examples
    --------
    >>> Alert(message="Fleet availability critical", severity="critical",
    ...       scope={"pit": "north"}).severity
    'critical'
    """

    message: str
    severity: Literal["low", "medium", "high", "critical"]
    scope: Mapping[str, str]
    triggered_by: ThresholdBreach | None = dataclasses.field(default=None, kw_only=True)

    def _normalize(self) -> None:
        super(Alert, self)._normalize()
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))


@dataclasses.dataclass(frozen=True, slots=True)
class RootCauseResult(DecisionResult):
    """The outcome of a :class:`~mineproductivity.decision.root_cause.RootCauseAnalyzer`
    (design spec §18) -- a future phase's interface-only extension point;
    this result type is implemented now even though no producer of it
    ships in this phase.

    Examples
    --------
    >>> RootCauseResult(
    ...     candidate_causes=("conveyor belt wear",),
    ...     confidence=ConfidenceScore(value=0.6, basis="rule_strength"),
    ... ).candidate_causes
    ('conveyor belt wear',)
    """

    candidate_causes: tuple[str, ...]
    confidence: ConfidenceScore


@dataclasses.dataclass(frozen=True, slots=True)
class WhatIfResult(DecisionResult):
    """The outcome of a :class:`~mineproductivity.decision.what_if.WhatIfEngine`
    (design spec §19) -- a future phase's interface-only extension point;
    this result type is implemented now even though no producer of it
    ships in this phase.

    Examples
    --------
    >>> WhatIfResult(
    ...     hypothesis={"shift_length_hours": 10}, predicted_outcome="OEE improves by 2%",
    ...     confidence=ConfidenceScore(value=0.4, basis="rule_strength"),
    ... ).predicted_outcome
    'OEE improves by 2%'
    """

    hypothesis: Mapping[str, Any]
    predicted_outcome: str
    confidence: ConfidenceScore

    def _normalize(self) -> None:
        super(WhatIfResult, self)._normalize()
        object.__setattr__(self, "hypothesis", MappingProxyType(dict(self.hypothesis)))
