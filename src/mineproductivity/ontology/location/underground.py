"""``Level``, ``Stope``, ``Drive``: underground structural entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Drive", "Level", "Stope"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Level(BaseEntityType):
    """Underground sibling of
    :class:`~mineproductivity.ontology.location.pit.Bench`: a horizontal
    working level within an underground mine."""

    code: ClassVar[str] = "LEVEL"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Level",
        description="A horizontal working level within an underground mine.",
        parent_code="BENCH",
    )

    mine_id: str
    elevation_m: float

    def validate(self) -> None:
        if not self.mine_id.strip():
            raise OntologyValidationError("Level.mine_id must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Stope(BaseEntityType):
    """A stope: an underground void created by ore extraction."""

    code: ClassVar[str] = "STOPE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Stope",
        description="An underground void created by ore extraction.",
    )

    level_id: str
    mining_method: str = dataclasses.field(default="", kw_only=True)

    def validate(self) -> None:
        if not self.level_id.strip():
            raise OntologyValidationError("Stope.level_id must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Drive(BaseEntityType):
    """An underground drive (horizontal access tunnel) connecting a level
    to a stope or another drive."""

    code: ClassVar[str] = "DRIVE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Drive",
        description="An underground horizontal access tunnel.",
    )

    level_id: str
    length_m: float = dataclasses.field(default=0.0, kw_only=True)

    def validate(self) -> None:
        if not self.level_id.strip():
            raise OntologyValidationError("Drive.level_id must not be empty")
