"""Drilling equipment types."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import EntityTypeMetadata, register_entity_type
from mineproductivity.ontology.equipment.equipment_type import EquipmentType

__all__ = ["BlastholeDrill"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class BlastholeDrill(EquipmentType):
    """A blasthole drill rig, preparing a bench for blasting."""

    code: ClassVar[str] = "BLASTHOLE_DRILL"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Blasthole Drill",
        description="A rotary or DTH blasthole drill rig used to prepare a bench for blasting.",
        supported_kpis=("UTIL.PA", "UTIL.UA", "DRILL.PenetrationRate"),
    )

    model: str = dataclasses.field(default="", kw_only=True)
    hole_diameter_mm: float = dataclasses.field(default=0.0, kw_only=True)
