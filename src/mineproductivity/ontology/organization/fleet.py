"""``Fleet``: a named group of equipment of one type."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Fleet"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Fleet(BaseEntityType):
    """A named group of equipment of one :class:`~mineproductivity.ontology.equipment.equipment_type.EquipmentType`.

    Examples
    --------
    >>> fleet = Fleet(id="FL-NORTH", mine_id="pilbara-ridge", equipment_type_code="RIGID_HAUL_TRUCK")
    >>> fleet.equipment_type_code
    'RIGID_HAUL_TRUCK'
    """

    code: ClassVar[str] = "FLEET"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Fleet",
        description="A named group of equipment of one equipment type.",
        supported_kpis=("HAUL.MatchFactor",),
    )

    mine_id: str
    equipment_type_code: str  # which EquipmentType.code this fleet aggregates

    def validate(self) -> None:
        if not self.equipment_type_code.strip():
            raise OntologyValidationError("Fleet.equipment_type_code must not be empty")
