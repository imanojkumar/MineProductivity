"""``Route`` and ``Zone``: haulage network entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Route", "Zone"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Zone(BaseEntityType):
    """A named area within a mine (a dump, a stockpile, a haul-road
    segment, a geofenced hazard area, ...). The generic location unit
    other entities (:class:`Route`, a future
    :class:`~mineproductivity.ontology.safety.hazard.HazardZone`) attach
    speed limits, distances, and other spatial attributes to.
    """

    code: ClassVar[str] = "ZONE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Zone",
        description="A named area within a mine (dump, stockpile, haul-road segment, ...).",
    )

    mine_id: str
    zone_type: str = dataclasses.field(default="general", kw_only=True)

    def validate(self) -> None:
        if not self.mine_id.strip():
            raise OntologyValidationError("Zone.mine_id must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Route(BaseEntityType):
    """A haul route: a source -> destination pair with a one-way distance.

    Examples
    --------
    >>> route = Route(
    ...     id="B7N_CR1", source_zone_id="B7N", destination_zone_id="CR1",
    ...     one_way_km=3.2, effective_grade_pct=8.5,
    ... )
    >>> route.one_way_km
    3.2
    """

    code: ClassVar[str] = "ROUTE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Route",
        description="A haul route: a source -> destination pair with a one-way distance.",
        supported_kpis=("HAUL.TonKm", "ENERGY.FuelPerTonne", "HAUL.EffectiveGrade"),
    )

    source_zone_id: str
    destination_zone_id: str
    one_way_km: float
    effective_grade_pct: float

    def validate(self) -> None:
        if self.one_way_km < 0:
            raise OntologyValidationError("Route.one_way_km must be >= 0")
