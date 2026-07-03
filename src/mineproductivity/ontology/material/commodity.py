"""``Commodity``: the mineral commodity a mine or pit produces."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Commodity"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Commodity(BaseEntityType):
    """A mineral commodity, e.g. copper, iron ore, gold.

    Examples
    --------
    >>> copper = Commodity(id="copper", symbol="Cu", unit_basis="tonnes")
    >>> copper.symbol
    'Cu'
    """

    code: ClassVar[str] = "COMMODITY"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Commodity",
        description="A mineral commodity a mine or pit produces (e.g. copper, iron ore, gold).",
    )

    symbol: str  # e.g. "Cu", "Fe", "Au"
    unit_basis: str  # "tonnes", "ounces", ...

    def validate(self) -> None:
        if not self.symbol.strip():
            raise OntologyValidationError("Commodity.symbol must not be empty")
        if not self.unit_basis.strip():
            raise OntologyValidationError("Commodity.unit_basis must not be empty")
