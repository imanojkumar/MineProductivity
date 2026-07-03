"""``DISP`` namespace flagship: total delay hours."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.delay_kpi import DelayKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["TotalDelayHours"]


@register
class TotalDelayHours(DelayKPI):
    """``sum(duration_h)`` across every recorded delay -- the headline
    number every delay-category breakdown starts from."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="DISP.TotalDelayHours",
        name="Total Delay Hours",
        official_name="Total Delay Hours",
        business_purpose="The single number every delay-category breakdown (Cookbook Part III) is a decomposition of.",
        operational_question="How many hours were lost to delay of any kind in this window?",
        business_meaning="Total delay hours falling while operating hours hold steady indicates a genuine improvement, not a measurement change.",
        formula="sum(duration_min) / 60",
        unit="h",
        dimensions=("Shift", "Day", "Equipment", "Fleet", "Mine"),
        required_events=("DELAY",),
        required_ontology=("Equipment", "Shift"),
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        edge_cases=(
            "no delay events in window -> 0.0, not None (an empty sum is a legitimate zero)",
        ),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("UTIL.PA", "UTIL.UA"),
        references=("Developer & Cookbook Guide Part III, Canonical Semantics (delay taxonomy)",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("duration_h",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return float(sum(row["duration_h"] for row in rows))
