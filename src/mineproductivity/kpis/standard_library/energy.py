"""``ENERGY`` namespace flagship: total fuel consumed."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.events import ResourceType

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.energy_kpi import EnergyKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["FuelConsumed"]


@register
class FuelConsumed(EnergyKPI):
    """``sum(quantity)`` across every fuel
    :class:`~mineproductivity.events.ConsumptionEvent` reading."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="ENERGY.FuelConsumed",
        name="Fuel Consumed",
        official_name="Fuel Consumed",
        business_purpose="The raw fuel volume every fuel-efficiency ratio (e.g. COST.FuelPerTonne) is built on.",
        operational_question="How much fuel did this fleet/asset consume in this window?",
        business_meaning="A rising trend with stable production points to an efficiency, not a volume, problem.",
        formula="sum(quantity) for resource_type == FUEL",
        unit="L",
        dimensions=("Shift", "Day", "Equipment", "Fleet"),
        required_events=("CONSUMPTION",),
        required_ontology=("Equipment",),
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("no fuel readings in window -> 0.0, not None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("COST.FuelPerTonne", "CARBON.CO2PerTonne"),
        references=("Developer & Cookbook Guide Part III, ENERGY namespace",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("resource_type", "quantity")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return float(
            sum(row["quantity"] for row in rows if row["resource_type"] is ResourceType.FUEL)
        )
