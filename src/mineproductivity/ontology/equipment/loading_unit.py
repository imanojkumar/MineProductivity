"""Loading unit equipment types."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import EntityTypeMetadata, register_entity_type
from mineproductivity.ontology.equipment.equipment_type import EquipmentType

__all__ = ["HydraulicShovel", "LHD", "WheelLoader"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class HydraulicShovel(EquipmentType):
    """A hydraulic face shovel that loads trucks."""

    code: ClassVar[str] = "HYDRAULIC_SHOVEL"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Hydraulic Shovel",
        description="A hydraulic face shovel loading trucks from a bench face.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "LOAD.Rate", "HAUL.MatchFactor"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    fleet_id: str | None = dataclasses.field(default=None, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class WheelLoader(EquipmentType):
    """A wheeled front-end loader, used for loading, stockpile rehandling,
    or as a secondary loading unit."""

    code: ClassVar[str] = "WHEEL_LOADER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Wheel Loader",
        description="A wheeled front-end loader used for loading or material rehandling.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "LOAD.Rate"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    fleet_id: str | None = dataclasses.field(default=None, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class LHD(EquipmentType):
    """A Load-Haul-Dump unit -- the underground counterpart to a surface
    loader/truck pairing, combining loading and short-haul tramming."""

    code: ClassVar[str] = "LHD"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Load-Haul-Dump Unit",
        description="An underground load-haul-dump unit for stope mucking and short tramming.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "PROD.TruckCycleTime"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    fleet_id: str | None = dataclasses.field(default=None, kw_only=True)
