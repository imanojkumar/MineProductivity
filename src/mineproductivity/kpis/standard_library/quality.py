"""``QUAL`` namespace flagship: the ore proportion of hauled material."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.quality_kpi import QualityKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["OreProportion"]


@register
class OreProportion(QualityKPI):
    """``count(material_type == "ore") / count(all cycles)`` -- the share
    of hauled material classified as ore rather than waste."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="QUAL.OreProportion",
        name="Ore Proportion",
        official_name="Ore Proportion",
        business_purpose="A cheap, always-available proxy for mining-sequence adherence ahead of assay-based grade KPIs.",
        operational_question="What share of hauled cycles this window were ore, not waste?",
        business_meaning="A falling ore proportion against the mine plan is an early signal worth an assay follow-up.",
        formula="count(material_type == 'ore') / count(cycles)",
        unit="ratio",
        dimensions=("Shift", "Day", "Pit", "Mine"),
        required_events=("CYCLE",),
        required_ontology=("Commodity", "Pit"),
        aggregation=Aggregation.RATIO,
        direction=Direction.TARGET_IS_BEST,
        min_maturity=DigitalMaturity.L1_MANUAL,
        edge_cases=("zero cycles in window -> None",),
        leading_or_lagging="leading",
        operational_or_strategic="operational",
        related_kpis=("GRADE.HeadGrade", "QUAL.Recovery"),
        references=("Developer & Cookbook Guide Part III, QUAL namespace",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("material_type",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        if not rows:
            return None
        ore_count = sum(1 for row in rows if row["material_type"] == "ore")
        return ore_count / len(rows)
