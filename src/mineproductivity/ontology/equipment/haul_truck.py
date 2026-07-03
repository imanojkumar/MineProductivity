"""Haul truck equipment types."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import EntityTypeMetadata, register_entity_type
from mineproductivity.ontology.equipment.equipment_type import EquipmentType

__all__ = ["ArticulatedHaulTruck", "RigidHaulTruck"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class RigidHaulTruck(EquipmentType):
    """A rigid-frame haul truck (e.g. CAT 793, Komatsu 930E)."""

    code: ClassVar[str] = "RIGID_HAUL_TRUCK"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Rigid Haul Truck",
        description="A rigid-frame, off-highway haul truck used for open-pit ore/waste haulage.",
        supported_kpis=(
            "PROD.TruckCycleTime",
            "PROD.Payload",
            "UTIL.PA",
            "UTIL.UA",
            "HAUL.TKPH",
            "HAUL.MatchFactor",
        ),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    fuel_type: str = dataclasses.field(default="diesel", kw_only=True)
    fleet_id: str | None = dataclasses.field(default=None, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class ArticulatedHaulTruck(EquipmentType):
    """An articulated (frame-steered) haul truck, typically used
    underground or on poor-condition surface haul roads."""

    code: ClassVar[str] = "ARTICULATED_HAUL_TRUCK"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Articulated Haul Truck",
        description="A frame-steered haul truck suited to tight, uneven, or underground haul routes.",
        supported_kpis=("PROD.TruckCycleTime", "PROD.Payload", "UTIL.PA", "UTIL.UA"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    fuel_type: str = dataclasses.field(default="diesel", kw_only=True)
    fleet_id: str | None = dataclasses.field(default=None, kw_only=True)
