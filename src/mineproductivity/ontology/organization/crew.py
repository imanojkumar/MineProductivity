"""``Crew`` and ``Operator``: the people who run the equipment."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Crew", "Operator"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Crew(BaseEntityType):
    """A rostered crew (e.g. "A", "B", "C", "D") working a shift pattern."""

    code: ClassVar[str] = "CREW"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Crew",
        description="A rostered crew working a shift pattern.",
    )

    mine_id: str

    def validate(self) -> None:
        if not self.mine_id.strip():
            raise OntologyValidationError("Crew.mine_id must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Operator(BaseEntityType):
    """An equipment operator, linked to cycle and delay events for
    operator-level KPI dimensions.

    Examples
    --------
    >>> op = Operator(id="OP-001", crew_id="A", licence_class="Haul Truck")
    >>> op.licence_class
    'Haul Truck'
    """

    code: ClassVar[str] = "OPERATOR"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Operator",
        description="An equipment operator.",
    )

    crew_id: str
    licence_class: str

    def validate(self) -> None:
        if not self.crew_id.strip():
            raise OntologyValidationError("Operator.crew_id must not be empty")
