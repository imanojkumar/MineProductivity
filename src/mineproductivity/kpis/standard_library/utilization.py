"""``UTIL`` namespace flagships: Physical Availability, Use of
Availability, a Performance ratio, and the composite Overall Equipment
Effectiveness -- built on the canonical time-model ladder (design spec
§19): ``calendar_h >= scheduled_h >= available_h >= operating_h``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.utilization_kpi import UtilizationKPI
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata
from mineproductivity.kpis.result import KPIResult

__all__ = [
    "OverallEquipmentEffectiveness",
    "PerformanceRatio",
    "PhysicalAvailability",
    "UseOfAvailability",
]


@register
class PhysicalAvailability(UtilizationKPI):
    """``available_h / scheduled_h`` -- the fraction of scheduled time an
    asset was mechanically available (not in unplanned downtime).

    ``available_h`` is derived here as ``scheduled_h`` minus summed
    unplanned :class:`~mineproductivity.events.MaintenanceEvent`
    downtime; ``scheduled_h`` comes from the scope's resolved
    :class:`~mineproductivity.ontology.Shift` (injected by
    :class:`~mineproductivity.kpis.engine.KPIEngine`).
    """

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="UTIL.PA",
        name="Physical Availability",
        official_name="Physical Availability",
        business_purpose="Availability is the foundation of the utilisation ladder every other UTIL KPI builds on.",
        operational_question="What fraction of scheduled time was this asset mechanically available?",
        business_meaning="Low PA points to a maintenance/reliability problem, not an operational one.",
        formula="available_h / scheduled_h, where available_h = scheduled_h - unplanned_downtime_h",
        unit="ratio",
        dimensions=("Shift", "Day", "Equipment", "Fleet"),
        required_events=("MAINTENANCE",),
        required_ontology=("Equipment", "Shift"),
        aggregation=Aggregation.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=(
            "scheduled_h == 0 -> None",
            "zero MaintenanceEvent rows in the window -> None "
            "(scheduled_h is carried on MaintenanceEvent rows only; with none, it is unknowable here)",
        ),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("UTIL.UA", "UTIL.OEE"),
        references=("Developer & Cookbook Guide Part III, Canonical Semantics",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("scheduled_h", "duration_h")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        if not rows:
            return None
        scheduled_h = rows[0]["scheduled_h"]
        if scheduled_h == 0:
            return None
        downtime_h = sum(row["duration_h"] for row in rows)
        available_h = scheduled_h - downtime_h
        return float(available_h / scheduled_h)


@register
class UseOfAvailability(UtilizationKPI):
    """``operating_h / available_h`` -- the fraction of *available* time an
    asset actually spent operating, reading both
    :class:`~mineproductivity.events.MaintenanceEvent` (for
    ``available_h``, the same derivation as :class:`PhysicalAvailability`)
    and :class:`~mineproductivity.events.ProductionEvent` (for
    ``operating_h``).
    """

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="UTIL.UA",
        name="Use of Availability",
        official_name="Use of Availability",
        business_purpose="Distinguishes 'asset was available but idle' from 'asset was unavailable.'",
        operational_question="Of the time this asset was available, how much of it was actually used?",
        business_meaning="Low UA with high PA points to a dispatch/utilisation problem, not a maintenance one.",
        formula="operating_h / available_h, where available_h = scheduled_h - unplanned_downtime_h",
        unit="ratio",
        dimensions=("Shift", "Day", "Equipment", "Fleet"),
        required_events=("MAINTENANCE", "PRODUCTION"),
        required_ontology=("Equipment", "Shift"),
        aggregation=Aggregation.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("available_h <= 0 -> None", "no ProductionEvent rows -> None"),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("UTIL.PA", "UTIL.OEE"),
        references=("Developer & Cookbook Guide Part III, Canonical Semantics",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("event_type_code", "scheduled_h")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        maintenance_rows = [row for row in rows if row["event_type_code"] == "MAINTENANCE"]
        production_rows = [row for row in rows if row["event_type_code"] == "PRODUCTION"]
        if not production_rows:
            return None
        scheduled_h = rows[0]["scheduled_h"]
        if scheduled_h == 0:
            return None
        downtime_h = sum(row["duration_h"] for row in maintenance_rows)
        available_h = scheduled_h - downtime_h
        if available_h <= 0:
            return None
        operating_h = sum(row["operating_h"] for row in production_rows)
        return float(operating_h / available_h)


@register
class PerformanceRatio(UtilizationKPI):
    """``tonnes_moved / planned_tonnes`` -- actual production against the
    shift plan, the "Performance" factor of Overall Equipment
    Effectiveness."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="UTIL.Performance",
        name="Performance Ratio",
        official_name="Performance Ratio",
        business_purpose="Captures under-performance against plan even when PA and UA both look healthy.",
        operational_question="Given the hours worked, how close to the planned rate did production come?",
        business_meaning="A Performance ratio below 1.0 means realized production trailed the shift plan.",
        formula=(
            "sum(tonnes_moved) / sum(planned_tonnes), both accumulated over the same "
            "operating_h window (Nakajima's Performance factor: realized rate vs. planned "
            "rate over time actually worked, not a raw availability ratio)"
        ),
        unit="ratio",
        dimensions=("Shift", "Day", "Pit", "Mine"),
        required_events=("PRODUCTION",),
        required_ontology=("Shift",),
        aggregation=Aggregation.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("sum(planned_tonnes) == 0 -> None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("UTIL.OEE", "PROD.TPH"),
        references=("Developer & Cookbook Guide Part III, Canonical Semantics",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("tonnes_moved", "planned_tonnes")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        planned = sum(row["planned_tonnes"] for row in rows)
        return None if planned == 0 else sum(row["tonnes_moved"] for row in rows) / planned


@register
class OverallEquipmentEffectiveness(UtilizationKPI, CompositeKPI):
    """``UTIL.OEE = UTIL.PA x UTIL.UA x UTIL.Performance`` -- a valid
    three-factor OEE formulation (Part III, Canonical Semantics).

    This reference implementation does not include a fourth Quality
    factor: that requires a dedicated grade/reject-rate event stream not
    yet part of this milestone's ``events`` canonical catalogue (see
    :class:`~mineproductivity.kpis.standard_library.quality.OreProportion`
    for a standalone, grade-adjacent ratio computed from what *is*
    available today).
    """

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="UTIL.OEE",
        name="Overall Equipment Effectiveness",
        official_name="Overall Equipment Effectiveness",
        business_purpose="The single composite number summarizing availability, utilisation, and performance together.",
        operational_question="Overall, how effectively was this asset's scheduled time converted to output?",
        business_meaning="OEE multiplies three independent loss factors; a low OEE always traces back to one of them.",
        formula="UTIL.PA * UTIL.UA * UTIL.Performance",
        unit="ratio",
        dimensions=("Shift", "Day", "Equipment", "Fleet"),
        required_events=("MAINTENANCE", "PRODUCTION"),
        required_ontology=("Equipment", "Shift"),
        dependencies=("UTIL.PA", "UTIL.UA", "UTIL.Performance"),
        aggregation=Aggregation.DERIVED,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L3_ANALYTICS,
        edge_cases=("any component KPI is None -> None, never a fabricated zero",),
        leading_or_lagging="lagging",
        operational_or_strategic="strategic",
        related_kpis=("UTIL.PA", "UTIL.UA", "UTIL.Performance"),
        references=("Developer & Cookbook Guide Part III, Canonical Semantics",),
    )

    def _combine(self, component_results: Mapping[str, KPIResult]) -> float | None:
        pa = component_results["UTIL.PA"].value
        ua = component_results["UTIL.UA"].value
        performance = component_results["UTIL.Performance"].value
        if pa is None or ua is None or performance is None:
            return None
        return pa * ua * performance
