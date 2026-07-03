"""``KPIValidator``: registration-time semantic validation beyond
``KPIMetadata.validate()`` (design spec §19's third layer: canonical
semantics).
"""

from __future__ import annotations

from mineproductivity.core import BaseValidator, ValidationResult

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.categories.utilization_kpi import UtilizationKPI
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation

__all__ = ["KPIValidator"]

#: The canonical time-model ladder (design spec §19): ``calendar_h >=
#: scheduled_h >= available_h >= operating_h``. A best-effort textual
#: check, since ``KPIMetadata.formula`` is a documentation string, not a
#: parsed DSL.
CANONICAL_TIME_MODEL_TERMS = ("scheduled_h", "available_h", "operating_h", "calendar_h")


class KPIValidator(BaseValidator[type[BaseKPI]]):
    """Registration-time semantic validation the engine enforces as
    invariants no KPI can override (design spec §19):

    - Every leaf (non-composite)
      :class:`~mineproductivity.kpis.categories.utilization_kpi.UtilizationKPI`'s
      formula must reference the canonical time-model ladder. A
      :class:`~mineproductivity.kpis.composite.CompositeKPI` is exempt
      from this specific textual check: its own formula composes other
      KPI codes' *results* (e.g. ``UTIL.OEE``'s ``UTIL.PA * UTIL.UA *
      UTIL.Performance``), not raw hour fields directly, and each
      dependency is independently validated when it is itself
      registered -- checking a composite's formula string for hour
      -field substrings would either be vacuously false or require
      duplicating its dependencies' formulas verbatim.
    - ``Aggregation.DERIVED`` is reserved for
      :class:`~mineproductivity.kpis.composite.CompositeKPI` subclasses.
    - A :class:`CompositeKPI` must declare at least one dependency (it
      has nothing to combine otherwise).
    """

    def validate(self, candidate: type[BaseKPI]) -> ValidationResult:
        errors: list[str] = []
        meta = candidate.meta

        if (
            issubclass(candidate, UtilizationKPI)
            and not issubclass(candidate, CompositeKPI)
            and not any(term in meta.formula for term in CANONICAL_TIME_MODEL_TERMS)
        ):
            errors.append(
                f"{meta.code}: a UtilizationKPI's formula must reference the canonical "
                f"time-model ladder ({', '.join(CANONICAL_TIME_MODEL_TERMS)})"
            )

        if meta.aggregation is Aggregation.DERIVED and not issubclass(candidate, CompositeKPI):
            errors.append(
                f"{meta.code}: aggregation=DERIVED is reserved for CompositeKPI subclasses"
            )

        if issubclass(candidate, CompositeKPI) and not meta.dependencies:
            errors.append(f"{meta.code}: a CompositeKPI must declare at least one dependency")

        return ValidationResult.success() if not errors else ValidationResult.failure(*errors)
