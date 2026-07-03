"""Fixed plant equipment types."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import EntityTypeMetadata, register_entity_type
from mineproductivity.ontology.equipment.equipment_type import EquipmentType

__all__ = ["Conveyor", "Crusher", "Mill"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Crusher(EquipmentType):
    """A fixed or semi-mobile crusher unit."""

    code: ClassVar[str] = "CRUSHER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Crusher",
        description="A fixed or semi-mobile crushing unit reducing run-of-mine material.",
        supported_kpis=("CRUSH.Throughput", "UTIL.OEE", "CRUSH.Utilisation"),
    )

    throughput_capacity_tph: float = dataclasses.field(default=0.0, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Conveyor(EquipmentType):
    """A fixed conveyor segment moving material between plant stages."""

    code: ClassVar[str] = "CONVEYOR"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Conveyor",
        description="A fixed conveyor segment transporting material between plant stages.",
        supported_kpis=("UTIL.PA", "UTIL.UA"),
    )

    length_m: float = dataclasses.field(default=0.0, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Mill(EquipmentType):
    """A grinding mill (SAG/ball/rod) reducing crushed ore to process feed size."""

    code: ClassVar[str] = "MILL"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Mill",
        description="A grinding mill reducing crushed ore to process feed size.",
        supported_kpis=("PROC.ConcentrateGrade", "UTIL.OEE"),
    )

    mill_type: str = dataclasses.field(default="ball", kw_only=True)
