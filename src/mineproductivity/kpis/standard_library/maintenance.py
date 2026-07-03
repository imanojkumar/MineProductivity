"""``MAINT`` namespace flagship: Mean Time To Repair."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.maintenance_kpi import MaintenanceKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["MeanTimeToRepair"]


@register
class MeanTimeToRepair(MaintenanceKPI):
    """``mean(total_downtime_h)`` across failure events -- how long, on
    average, an asset stays down once it fails."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="MAINT.MTTR",
        name="Mean Time To Repair",
        official_name="Mean Time To Repair",
        business_purpose="MTTR is the maintenance team's own headline responsiveness metric.",
        operational_question="Once a failure happens, how long does it typically take to return to service?",
        business_meaning="A rising MTTR signals a repair-capability problem (parts, crew, diagnostics), not a reliability one.",
        formula="sum(total_downtime_h) / count(failures)",
        unit="h",
        dimensions=("Shift", "Day", "Week", "Equipment", "Fleet"),
        required_events=("MAINTENANCE",),
        required_ontology=("Equipment", "FailureMode"),
        aggregation=Aggregation.AVERAGE,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("zero failures in window -> None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("MAINT.MTBF", "MAINT.Ai"),
        references=("Developer & Cookbook Guide Part III, MAINT namespace",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("duration_h",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return None if not rows else sum(row["duration_h"] for row in rows) / len(rows)
