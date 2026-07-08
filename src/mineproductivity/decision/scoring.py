"""Decision scoring and confidence scoring (design spec §23, §24).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``analytics.DataQualityScore`` is read directly, never recomputed --
``ConfidenceScorer`` searches ``DecisionContext.analytics_results`` for
an already-produced instance rather than re-deriving completeness/
validity itself (design spec §3.2, §24's own "never recomputing data
quality itself" mandate). No existing table anywhere in ``core``,
``registry``, ``events``, ``kpis``, or ``analytics`` maps a decision
severity level to a numeric weight -- ``_SEVERITY_WEIGHTS`` below is
therefore a genuinely new, minimal lookup table, not a duplicate of an
existing one. It is deliberately defined *here*, in ``scoring.py`` (not
in ``result.py`` or duplicated per-module), so ``prioritization.py``
can import and reuse the same table for its own severity-driven
``urgency`` component rather than defining a second, possibly-drifting
copy -- see ``prioritization.py``'s own reuse-audit note.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from mineproductivity.analytics import DataQualityScore

from mineproductivity.decision.abstractions import DecisionContext
from mineproductivity.decision.result import ConfidenceScore, DecisionScore, Recommendation

__all__ = ["ConfidenceScorer", "DecisionScorer"]

#: Neither ``Policy`` (§12) nor ``Recommendation`` (§15) carries a
#: numeric severity weight -- both are specified as plain, un-weighted
#: business/output data. This fixed, disclosed mapping is the smallest
#: compatible resolution: a reasonable, deterministic default that
#: does not add an undocumented field to either already-specified,
#: locked value object. Reused verbatim by ``prioritization.py``.
_SEVERITY_WEIGHTS: Mapping[Literal["low", "medium", "high", "critical"], float] = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}

#: The number of triggered rules beyond which corroboration strength is
#: treated as maximal (§23's "policy weight" / §24's "rule strength"
#: component) -- a fixed, disclosed cap, not a caller-configurable
#: threshold, since neither the design spec nor ``Policy`` supplies one.
_MAX_CORROBORATING_RULES = 5


def _rule_strength(recommendation: Recommendation) -> float:
    """How strongly ``recommendation``'s own rule evidence corroborates
    it, in ``[0.0, 1.0]`` -- more triggered rules is a stronger signal,
    capped at :data:`_MAX_CORROBORATING_RULES`. Shared by both
    :class:`DecisionScorer` and :class:`ConfidenceScorer` so the two
    scorers never silently disagree on what "rule strength" means."""
    if not recommendation.triggered_rules:
        return 0.0
    return min(1.0, len(recommendation.triggered_rules) / _MAX_CORROBORATING_RULES)


class DecisionScorer:
    """Computes the numeric weight (:class:`DecisionScore`) backing
    ranking (§16) -- a function of severity, policy weight (approximated
    here as rule-corroboration strength, see :func:`_rule_strength`),
    and, optionally, :class:`ConfidenceScore` (§24) -- never of raw
    KPI/Analytics values directly re-interpreted.

    Examples
    --------
    >>> from mineproductivity.decision.result import ConfidenceScore
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="x", severity="critical", evidence=("UTIL.OEE",),
    ... )
    >>> score = DecisionScorer().score(rec, confidence=ConfidenceScore(value=1.0, basis="rule_strength"))
    >>> round(score.value, 4)
    0.84
    """

    def score(
        self, recommendation: Recommendation, *, confidence: ConfidenceScore | None = None
    ) -> DecisionScore:
        severity_weight = _SEVERITY_WEIGHTS[recommendation.severity]
        policy_weight = _rule_strength(recommendation)
        confidence_weight = confidence.value if confidence is not None else 1.0
        value = severity_weight * 0.5 + policy_weight * 0.2 + confidence_weight * 0.3
        return DecisionScore(
            value=value,
            components={
                "severity": severity_weight,
                "policy_weight": policy_weight,
                "confidence": confidence_weight,
            },
        )


class ConfidenceScorer:
    """Computes :class:`ConfidenceScore`, deriving from
    ``analytics.DataQualityScore`` (spec 06 §25) plus how many/which
    rules corroborated a ``Recommendation`` -- never recomputing data
    quality itself. Falls back to ``"rule_strength"`` basis when no
    ``DataQualityScore`` is present in ``context.analytics_results``.

    This scorer's own derivation never produces a bare ``"data_quality"``
    basis: a ``Recommendation`` always carries at least one triggered
    rule by construction (``Policy.validate()`` requires at least one
    rule), so rule-strength evidence is always present alongside any
    ``DataQualityScore`` that may also be found -- the result is always
    ``"rule_strength"`` alone or ``"combined"``. The third basis literal
    (``"data_quality"``) remains a legitimate value other producers may
    use; this class simply never has a reason to.

    Examples
    --------
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="x", severity="high", evidence=("UTIL.OEE",),
    ... )
    >>> context = DecisionContext(kpi_results=(), analytics_results=(), scope={})
    >>> ConfidenceScorer().score(rec, context=context).basis
    'rule_strength'
    """

    def score(self, recommendation: Recommendation, *, context: DecisionContext) -> ConfidenceScore:
        rule_strength = _rule_strength(recommendation)
        data_quality = next(
            (
                result
                for result in context.analytics_results
                if isinstance(result, DataQualityScore)
            ),
            None,
        )
        if data_quality is None:
            return ConfidenceScore(value=rule_strength, basis="rule_strength")
        combined = (data_quality.overall_score + rule_strength) / 2.0
        return ConfidenceScore(value=combined, basis="combined")
