"""``Mine``: the top-level site entity."""

from __future__ import annotations

import dataclasses
from typing import ClassVar, Literal


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Mine"]

MiningMethod = Literal["open_pit", "underground"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Mine(BaseEntityType):
    """The top-level mine site entity: a named operation producing one or
    more commodities under one mining method.

    Examples
    --------
    >>> mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
    >>> mine.method
    'open_pit'
    """

    code: ClassVar[str] = "MINE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Mine",
        description="The top-level mine site entity.",
    )

    commodity_codes: tuple[str, ...]
    method: MiningMethod

    def validate(self) -> None:
        if not self.commodity_codes:
            raise OntologyValidationError("Mine.commodity_codes must not be empty")
