"""``Threshold``: the declarative limit values a ``Policy``'s rules
reference (design spec §13).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
No existing value object in ``core``, ``kpis``, or ``analytics``
represents a comparator/limit pair over a named field -- this is a
genuinely new, minimal shape. ``Threshold`` is included in this
Foundation phase (ahead of ``rules.py``/``policy.py``/``strategy.py``,
all explicitly out of scope for this phase) only because
``result.py``'s ``ThresholdBreach`` -- one of this phase's required
"Decision result objects" (design spec §28) -- has a mandatory
``threshold: Threshold`` field and cannot be correctly typed without
it. ``Threshold`` itself carries zero decision/business logic (no rule
evaluation, no policy lifecycle) -- it is pure data, exactly as light as
``analytics.RollingSpec`` -- so including it here is a necessary,
minimal, disclosed addition to the Foundation phase's own module list,
not a scope violation into ``rules.py``/``policy.py``/``strategy.py``'s
"business-specific decision model" territory.
"""

from __future__ import annotations

import dataclasses
from typing import Literal

from mineproductivity.core import BaseValueObject

from mineproductivity.decision.exceptions import DecisionValidationError

__all__ = ["Threshold"]


@dataclasses.dataclass(frozen=True, slots=True)
class Threshold(BaseValueObject):
    """One declarative limit a ``Rule`` references, e.g.
    ``Threshold(field="value", comparator="<", limit=0.65)`` checked
    against the relevant ``KPIResult``/``AnalyticsResult`` field named by
    ``field``.

    Deliberately data, not code -- a ``Policy`` can be updated to
    reference a new limit value through ordinary version governance
    (design spec §12) without touching any ``Rule``'s predicate logic.

    Examples
    --------
    >>> Threshold(field="value", comparator="<", limit=0.65).limit
    0.65
    >>> Threshold(field="", comparator="<", limit=0.65)
    Traceback (most recent call last):
        ...
    mineproductivity.decision.exceptions.DecisionValidationError: Threshold.field must not be empty
    """

    field: str
    comparator: Literal["<", "<=", ">", ">=", "==", "!="]
    limit: float

    def validate(self) -> None:
        if not self.field.strip():
            raise DecisionValidationError("Threshold.field must not be empty")
