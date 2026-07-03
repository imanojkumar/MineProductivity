"""Ancillary equipment types."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import EntityTypeMetadata, register_entity_type
from mineproductivity.ontology.equipment.equipment_type import EquipmentType

__all__ = ["Dozer", "Grader", "WaterTruck"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Dozer(EquipmentType):
    """A track dozer used for rehandling, ripping, and dump/bench housekeeping."""

    code: ClassVar[str] = "DOZER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Dozer",
        description="A track dozer used for material rehandling, ripping, and housekeeping.",
        supported_kpis=("UTIL.PA", "UTIL.UA"),
    )

    model: str = dataclasses.field(default="", kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Grader(EquipmentType):
    """A motor grader used for haul road maintenance."""

    code: ClassVar[str] = "GRADER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Grader",
        description="A motor grader used for haul road maintenance and levelling.",
        supported_kpis=("UTIL.PA", "UTIL.UA"),
    )

    model: str = dataclasses.field(default="", kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class WaterTruck(EquipmentType):
    """A water truck used for haul-road dust suppression."""

    code: ClassVar[str] = "WATER_TRUCK"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Water Truck",
        description="A water truck used for dust suppression on haul roads.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "COST.FuelPerTonne"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    tank_capacity_l: float = dataclasses.field(default=0.0, kw_only=True)
