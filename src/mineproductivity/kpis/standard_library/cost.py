"""``COST`` namespace flagship: fuel cost per tonne hauled -- the exact
worked example from design spec §17's plugin walkthrough.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.events import ResourceType

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.cost_kpi import CostKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["FuelPerTonne"]


@register
class FuelPerTonne(CostKPI):
    """``sum(fuel_l) / sum(payload_t)`` -- fuel efficiency per tonne
    hauled, reading both
    :class:`~mineproductivity.events.ConsumptionEvent` (for fuel volume)
    and :class:`~mineproductivity.events.CycleEvent` (for payload).

    ``dependencies=("PROD.TPH",)`` matches design spec §17's own worked
    example verbatim -- ``_compute`` re-derives directly from raw rows
    (never from ``PROD.TPH``'s computed value; a non-composite KPI never
    receives dependency results, only raw rows, per
    :meth:`~mineproductivity.kpis.base_kpi.BaseKPI.compute`), so the
    declared dependency documents the thematic/DAG relationship the
    Standard Library groups these two KPIs under, ensuring ``PROD.TPH``
    is computed and cache-warmed alongside this KPI rather than gating
    ``_compute`` itself on it.
    """

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="COST.FuelPerTonne",
        name="Fuel Per Tonne",
        official_name="Fuel Per Tonne",
        business_purpose="Fuel is one of the largest controllable operating costs in mining; per-tonne is the comparable unit.",
        operational_question="How much fuel does it take to move one tonne of material right now?",
        business_meaning="A rising trend at stable payload/route indicates an efficiency problem, not a volume one.",
        formula="sum(fuel_l) / sum(payload_t)",
        unit="L/t",
        dimensions=("Shift", "Day", "Equipment", "Fleet"),
        required_events=("CONSUMPTION", "CYCLE"),
        required_ontology=("Equipment",),
        dependencies=("PROD.TPH",),
        aggregation=Aggregation.RATIO,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("sum(payload_t) == 0 -> None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("ENERGY.FuelConsumed", "PROD.TPH"),
        references=("Developer & Cookbook Guide Part III, §17 worked example",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("event_type_code",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        fuel_l = sum(
            row["quantity"]
            for row in rows
            if row["event_type_code"] == "CONSUMPTION" and row["resource_type"] is ResourceType.FUEL
        )
        payload_t = sum(row["payload_t"] for row in rows if row["event_type_code"] == "CYCLE")
        return None if payload_t == 0 else fuel_l / payload_t
