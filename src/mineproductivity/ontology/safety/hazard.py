"""``HazardZone``, ``SpeedLimitMap``, ``SafetyEventType``: safety reference entities.

``SafetyEventType`` is owned here, not by ``events``, for the identical
reason ``DelayCategory`` is owned here and not by ``events``: it is a
closed, governed taxonomy -- domain reference *data*, not event
*structure* (design spec AD-ON-03, applied by the same rationale).
``events.canonical.safety_event.SafetyEvent.safety_event_type`` imports
and consumes this enum rather than defining its own copy.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from enum import Enum
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["HazardZone", "SafetyEventType", "SpeedLimitMap"]


class SafetyEventType(Enum):
    """The leading safety-indicator kinds a safety event can record."""

    SPEED_VIOLATION = "speed-violation"
    FATIGUE = "fatigue"
    PROXIMITY = "proximity"
    SEATBELT = "seatbelt"


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class HazardZone(BaseEntityType):
    """A geofenced zone with a governed speed limit -- the reference a
    ``SAFE.SpeedViolationRate``-style KPI resolves "violation" against.

    Examples
    --------
    >>> zone = HazardZone(id="B7N_CR1", zone_id="B7N_CR1", speed_limit_kmh=45.0)
    >>> zone.speed_limit_kmh
    45.0
    """

    code: ClassVar[str] = "HAZARD_ZONE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Hazard Zone",
        description="A geofenced zone with a governed speed limit.",
        supported_kpis=("SAFE.SpeedViolationRate",),
    )

    zone_id: str
    speed_limit_kmh: float

    def validate(self) -> None:
        if self.speed_limit_kmh < 0:
            raise OntologyValidationError("HazardZone.speed_limit_kmh must be >= 0")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class SpeedLimitMap(BaseEntityType):
    """A mine-wide map of zone id -> governed speed limit, the single
    source of truth ``SAFE.SpeedViolationRate`` and similar KPIs read to
    decide whether a given speed reading was a violation."""

    code: ClassVar[str] = "SPEED_LIMIT_MAP"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Speed Limit Map",
        description="A mine-wide map of zone id to governed speed limit.",
    )

    mine_id: str
    zone_limits_kmh: Mapping[str, float] = dataclasses.field(default_factory=dict, kw_only=True)

    def validate(self) -> None:
        if not self.mine_id.strip():
            raise OntologyValidationError("SpeedLimitMap.mine_id must not be empty")
        if any(limit < 0 for limit in self.zone_limits_kmh.values()):
            raise OntologyValidationError("SpeedLimitMap.zone_limits_kmh values must be >= 0")
