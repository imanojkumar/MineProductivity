"""Action prioritization (design spec §20) -- a distinct question from
ranking (§16): "the single best recommendation is not always the one
with the most execution capacity available to act on it right now."

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``urgency`` reuses ``scoring._SEVERITY_WEIGHTS`` verbatim rather than
defining a second severity-to-float table -- both concepts read the
same ``Recommendation.severity`` field and there is no reason for them
to ever disagree on what "critical" numerically means. ``impact``
reuses the ``DecisionScore.value`` a ``RankedRecommendation`` already
carries (design spec §20's own explicit instruction: "impact derives
from the DecisionScore the recommendation already carries") -- no
second impact computation is introduced. ``effort`` has no informing
field anywhere in the already-specified, locked ``Policy``/
``Recommendation`` shapes (design spec §20's own prose: "effort is a
site-specific estimate a Policy or a caller supplies, since this
package has no basis of its own for estimating how long an
intervention takes") -- ``ActionPrioritizer.prioritize()``'s own
signature is fixed by §20's pseudocode with no room for a per-call
effort argument, so a constructor-level, caller-suppliable
``effort_estimates`` mapping (keyed by ``Recommendation.policy_code``,
falling back to a disclosed default) is the smallest compatible
resolution -- an additive constructor parameter, not a change to any
locked value object's own fields.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from mineproductivity.decision.result import ActionPriority, RankedRecommendation
from mineproductivity.decision.scoring import _SEVERITY_WEIGHTS

__all__ = ["ActionPrioritizer"]


class ActionPrioritizer:
    """Given a ``Sequence[RankedRecommendation]``, assigns each an
    ``ActionPriority`` reflecting urgency/impact/effort under limited
    execution capacity.

    Examples
    --------
    >>> from mineproductivity.decision.result import DecisionScore, Recommendation
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="x", severity="high", evidence=(),
    ... )
    >>> ranked = RankedRecommendation(
    ...     recommendation=rec, score=DecisionScore(value=0.7, components={}), rank=1,
    ... )
    >>> prioritized = ActionPrioritizer().prioritize([ranked])
    >>> item, priority = prioritized[0]
    >>> priority.urgency, priority.impact
    (0.75, 0.7)
    """

    def __init__(
        self,
        *,
        effort_estimates: Mapping[str, float] | None = None,
        default_effort: float = 1.0,
    ) -> None:
        self._effort_estimates = dict(effort_estimates) if effort_estimates else {}
        self._default_effort = default_effort

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(effort_estimates={self._effort_estimates!r}, "
            f"default_effort={self._default_effort!r})"
        )

    def prioritize(
        self, ranked: Sequence[RankedRecommendation]
    ) -> Sequence[tuple[RankedRecommendation, ActionPriority]]:
        result = []
        for item in ranked:
            urgency = _SEVERITY_WEIGHTS[item.recommendation.severity]
            impact = item.score.value
            effort = self._effort_estimates.get(
                item.recommendation.policy_code, self._default_effort
            )
            result.append((item, ActionPriority(urgency=urgency, impact=impact, effort=effort)))
        return tuple(result)
