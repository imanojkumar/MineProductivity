"""``SAFE`` namespace flagship: speed-violation count."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from mineproductivity.ontology import SafetyEventType

from mineproductivity.kpis._registry import register
from mineproductivity.kpis.categories.safety_kpi import SafetyKPI
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata

__all__ = ["SpeedViolationCount"]


@register
class SpeedViolationCount(SafetyKPI):
    """``count(safety_event_type == SPEED_VIOLATION)`` -- an
    exposure-normalized-in-name-only leading indicator: the raw count of
    governed-zone speed violations, reading
    :class:`~mineproductivity.ontology.SafetyEventType` (the same,
    non-duplicated enum :class:`~mineproductivity.events.SafetyEvent`
    consumes)."""

    meta: ClassVar[KPIMetadata] = KPIMetadata(
        code="SAFE.SpeedViolationCount",
        name="Speed Violation Count",
        official_name="Speed Violation Count",
        business_purpose="Leading safety indicators catch risk before it becomes an incident.",
        operational_question="How many governed-zone speed violations were recorded this window?",
        business_meaning="A rising count at stable haul volume is an early behavioural signal, not statistical noise.",
        formula="count(safety_event_type == SPEED_VIOLATION)",
        unit="count",
        dimensions=("Shift", "Day", "Equipment", "Fleet", "Mine"),
        required_events=("SAFETY",),
        required_ontology=("HazardZone", "SpeedLimitMap"),
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.LOWER_IS_BETTER,
        min_maturity=DigitalMaturity.L2_FMS,
        edge_cases=("no safety events in window -> 0.0, not None",),
        leading_or_lagging="leading",
        operational_or_strategic="operational",
        related_kpis=("SAFE.SpeedViolationRate",),
        references=("Developer & Cookbook Guide Part III, SAFE namespace",),
    )

    def _required_columns(self) -> tuple[str, ...]:
        return ("safety_event_type",)

    def _compute(self, rows: Sequence[Mapping[str, Any]]) -> float | None:
        return float(
            sum(1 for row in rows if row["safety_event_type"] is SafetyEventType.SPEED_VIOLATION)
        )
