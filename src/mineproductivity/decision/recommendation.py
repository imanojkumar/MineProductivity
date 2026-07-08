"""Recommendation generation (design spec §15, §6 ``recommendation.py``).

Design spec §6 lists this module with **no public classes, functions, or
API of its own**: "the ``Recommendation`` type lives in ``result.py``;
this module holds the generation logic" invoked through
``ThresholdDecisionStrategy``'s methods (``strategy.py``), which
delegate here. :func:`build_recommendation` is therefore a
package-internal helper -- deliberately not re-exported from
``mineproductivity.decision``'s top-level ``__all__``, mirroring how
``policy.publish_policy`` satisfies a behavioral requirement without
expanding the public surface beyond what design spec §7 actually lists.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``result.Recommendation`` is reused verbatim as the one output type --
no second recommendation-shaped value object is introduced. The
summary-text format is the single, canonical one
``ThresholdDecisionStrategy`` established in Phase 07.2 (moved here
unchanged, not duplicated): every ``Recommendation`` produced through
this module names its ``Policy`` and every triggered rule, preserving
§15's "always traceable to specific ``Policy``/``Rule`` names"
guarantee. Dependencies are exactly the two design spec §6 declares for
this module -- ``result.py`` and ``policy.py``; evidence extraction
from a ``DecisionContext`` deliberately stays in ``strategy.py``, which
is the module §6 permits to depend on ``abstractions.py``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from mineproductivity.decision.policy import Policy
from mineproductivity.decision.result import Recommendation

__all__: list[str] = []


def build_recommendation(
    *,
    policy: Policy,
    triggered_rules: Sequence[str],
    evidence: Sequence[str],
    severity: Literal["low", "medium", "high", "critical"],
    model_code: str,
) -> Recommendation:
    """Produce one ``Recommendation`` from a ``DecisionStrategy``'s
    evaluation of a ``DecisionContext`` against an active ``Policy``
    (design spec §15) -- the generation logic ``ThresholdDecisionStrategy._decide``
    delegates to once rule evaluation has already established
    ``triggered_rules``.

    Package-internal (see module docstring): not part of
    ``mineproductivity.decision``'s public API.

    Examples
    --------
    >>> from mineproductivity.core import PredicateSpecification
    >>> policy = Policy(
    ...     code="AVAIL.LowFleetAvailability",
    ...     rules={"low_oee": PredicateSpecification(lambda ctx: True)},
    ...     strategy_code="STRATEGY.Threshold",
    ... )
    >>> recommendation = build_recommendation(
    ...     policy=policy, triggered_rules=("low_oee",), evidence=("UTIL.OEE",),
    ...     severity="high", model_code="STRATEGY.Threshold",
    ... )
    >>> recommendation.policy_code, recommendation.triggered_rules
    ('AVAIL.LowFleetAvailability', ('low_oee',))
    >>> recommendation.summary
    "Policy 'AVAIL.LowFleetAvailability' triggered by rule(s): low_oee"
    """
    return Recommendation(
        model_code=model_code,
        policy_code=policy.code,
        triggered_rules=tuple(triggered_rules),
        summary=f"Policy {policy.code!r} triggered by rule(s): {', '.join(triggered_rules)}",
        severity=severity,
        evidence=tuple(evidence),
    )
