"""``Pit`` and ``Bench``: open-pit structural entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Bench", "Pit"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Pit(BaseEntityType):
    """An open pit within a mine.

    Examples
    --------
    >>> west = Pit(id="pit-west", mine_id="bingham-west", commodity="copper")
    >>> west.mine_id
    'bingham-west'
    """

    code: ClassVar[str] = "PIT"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Pit",
        description="An open pit within a mine.",
    )

    mine_id: str
    commodity: str

    def validate(self) -> None:
        if not self.mine_id.strip():
            raise OntologyValidationError("Pit.mine_id must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Bench(BaseEntityType):
    """A bench (working level) within a pit.

    Examples
    --------
    >>> b7 = Bench(id="bench-7", pit_id="pit-west", elevation_m=1820.0)
    >>> b7.pit_id
    'pit-west'
    """

    code: ClassVar[str] = "BENCH"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Bench",
        description="A bench (working level) within a pit.",
    )

    pit_id: str
    elevation_m: float

    def validate(self) -> None:
        if not self.pit_id.strip():
            raise OntologyValidationError("Bench.pit_id must not be empty")
