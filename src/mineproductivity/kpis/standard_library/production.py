"""``PROD.TPH`` -- the design specification's own reference exemplar
(§10.5): payload moved per operating hour.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.production_kpi import ProductionKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["TonnesPerHour"]


@register
class TonnesPerHour(ProductionKPI):
    """Headline production rate: payload moved per operating hour.

    Business purpose: throughput rate is the single most-watched
    production number in mining. Operational question: at what rate is
    this asset producing material?
    """

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="PROD.TPH",
        name="Tonnes Per Hour",
        official_name="Tonnes Per Hour",
        business_purpose="Throughput rate is the single most-watched production number in mining.",
        operational_question="At what rate is this asset producing material?",
        business_meaning="A higher, stable TPH means efficient conversion of operating time to output.",
        formula="sum(payload_t) / sum(operating_h)",
        unit="t/h",
        dimensions=("Shift", "Day", "Equipment", "Fleet", "Pit", "Mine"),
        required_events=("CYCLE",),
        required_ontology=("Equipment", "Shift"),
        aggregation=Aggregation.RATIO,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        edge_cases=("operating_h == 0 -> None",),
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
        related_kpis=("PROD.TruckCycleTime", "PROD.Payload", "HAUL.MatchFactor"),
        references=("Developer & Cookbook Guide Part III, PROD.TPH",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("payload_t", "operating_h")

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        hours = sum(row["operating_h"] for row in rows)
        return None if hours == 0 else sum(row["payload_t"] for row in rows) / hours
