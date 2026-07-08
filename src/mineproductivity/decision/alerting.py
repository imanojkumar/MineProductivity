"""``AlertGenerator``: produces an ``Alert`` from a ``ThresholdBreach``
or a high-severity ``Recommendation`` (design spec §22).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``Alert`` and ``ThresholdBreach`` already exist in ``result.py`` (Phase
07.1, ahead of schedule) -- no new value type is introduced here.
``Recommendation.severity`` is read directly for :meth:`~AlertGenerator.from_recommendation`
rather than recomputed. A ``ThresholdBreach`` carries no severity field
of its own (only ``threshold``, ``observed_value``, ``breached_at``),
and the design spec states no magnitude-to-severity heuristic for
:meth:`~AlertGenerator.from_breach` -- rather than inventing one (which
would be exactly the kind of "ad hoc business logic" §33 already warns
against for ``DecisionStrategy`` subclasses, reapplied here), this
module reuses the same precedent ``strategy.ThresholdDecisionStrategy``
already established one phase earlier: severity is a caller/policy-
configured value (its own ``severity: Literal[...] = "medium"``
constructor parameter), not a value derived from data magnitude.
``AlertGenerator`` mirrors that exact convention via its own
``breach_severity`` constructor parameter.

Neither ``ThresholdBreach`` nor ``Recommendation`` carries a ``scope``
field the way ``DecisionContext`` does, yet ``Alert.scope`` is a
required field -- an optional ``scope`` keyword parameter, defaulting to
an empty mapping, is added to both methods as the smallest compatible
resolution, mirroring the identical ``dependencies: Mapping[...] =
MappingProxyType({})`` optional-mapping convention ``planning.ActionPlanner.plan``
already uses one section earlier in the same design spec (§21).
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

from mineproductivity.decision.result import Alert, Recommendation, ThresholdBreach

__all__ = ["AlertGenerator"]

_ALERTABLE_SEVERITIES = ("high", "critical")


class AlertGenerator:
    """Produces an ``Alert`` from a ``ThresholdBreach`` (§13) or a
    high-severity ``Recommendation`` (§15). A concrete, non-pluggable
    utility -- alert *channel* delivery (email, SMS, a dashboard push)
    is explicitly out of scope for this package (§4);
    ``AlertGenerator`` produces the ``Alert`` value object only, never
    sends it anywhere, keeping it a pure, easily-tested function with no
    I/O side effects.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> from mineproductivity.decision.thresholds import Threshold
    >>> breach = ThresholdBreach(
    ...     threshold=Threshold(field="value", comparator="<", limit=0.65),
    ...     observed_value=0.58, breached_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    ... )
    >>> AlertGenerator().from_breach(breach).severity
    'high'
    >>> rec = Recommendation(
    ...     policy_code="AVAIL.LowFleetAvailability", triggered_rules=("low_oee",),
    ...     summary="Investigate fleet availability", severity="critical", evidence=("UTIL.OEE",),
    ... )
    >>> AlertGenerator().from_recommendation(rec).message
    'Investigate fleet availability'
    >>> low_severity = Recommendation(
    ...     policy_code="X", triggered_rules=(), summary="x", severity="low", evidence=(),
    ... )
    >>> AlertGenerator().from_recommendation(low_severity) is None
    True
    """

    def __init__(
        self, *, breach_severity: Literal["low", "medium", "high", "critical"] = "high"
    ) -> None:
        self._breach_severity = breach_severity

    def from_breach(
        self, breach: ThresholdBreach, *, scope: Mapping[str, str] = MappingProxyType({})
    ) -> Alert:
        threshold = breach.threshold
        return Alert(
            message=(
                f"Threshold breached: {threshold.field} {threshold.comparator} "
                f"{threshold.limit} (observed {breach.observed_value})"
            ),
            severity=self._breach_severity,
            scope=scope,
            triggered_by=breach,
        )

    def from_recommendation(
        self, recommendation: Recommendation, *, scope: Mapping[str, str] = MappingProxyType({})
    ) -> Alert | None:
        if recommendation.severity not in _ALERTABLE_SEVERITIES:
            return None
        return Alert(message=recommendation.summary, severity=recommendation.severity, scope=scope)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(breach_severity={self._breach_severity!r})"
