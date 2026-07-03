"""``HAUL`` namespace flagship: average truck cycle time."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.haulage_kpi import HaulageKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

_LEGS = ("queue_min", "spot_min", "load_min", "haul_min", "dump_min", "return_min")

__all__ = ["TruckCycleTime"]


@register
class TruckCycleTime(HaulageKPI):
    """``mean(queue_min + spot_min + load_min + haul_min + dump_min +
    return_min)`` -- the average end-to-end haul cycle duration."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="HAUL.TruckCycleTime",
        name="Truck Cycle Time",
        official_name="Truck Cycle Time",
        business_purpose="Cycle time is the fundamental unit haulage throughput and match-factor analysis build on.",
        operational_question="How long, on average, does one haul cycle take on this route/fleet?",
        business_meaning="A rising cycle time with a stable route usually points to queueing, not haul-road conditions.",
        formula="mean(queue_min + spot_min + load_min + haul_min + dump_min + return_min)",
        unit="min",
        dimensions=("Shift", "Day", "Equipment", "Fleet", "Route"),
        required_events=("CYCLE",),
        required_ontology=("Equipment", "Route"),
        aggregation=Aggregation.AVERAGE,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        edge_cases=("zero cycles in window -> None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("PROD.TPH", "HAUL.MatchFactor"),
        references=("Developer & Cookbook Guide Part III, HAUL namespace",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return _LEGS

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        if not rows:
            return None
        totals = [sum(row[leg] for leg in _LEGS) for row in rows]
        return float(sum(totals) / len(totals))
