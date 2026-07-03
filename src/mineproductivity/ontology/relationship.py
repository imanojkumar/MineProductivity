"""``Relationship``: a declared, typed edge between two entity ids."""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseValueObject
from mineproductivity.ontology.exceptions import RelationshipError

__all__ = ["Relationship", "RelationshipKind"]


class RelationshipKind(Enum):
    """The five relationship kinds the ontology declares between entities."""

    BELONGS_TO = "belongs_to"  # Bench belongs_to Pit
    PART_OF = "part_of"  # Truck part_of Fleet
    OPERATED_BY = "operated_by"  # Equipment operated_by Operator
    LOCATED_AT = "located_at"  # Equipment located_at Zone
    SCOPED_TO = "scoped_to"  # CostCenter scoped_to BusinessUnit


@dataclasses.dataclass(frozen=True, slots=True)
class Relationship(BaseValueObject):
    """A declared, typed edge between two entity ids.

    Relationships are how "by pit" or "by fleet" slicing resolves: a
    :class:`~mineproductivity.ontology.location.pit.Bench` and a
    :class:`~mineproductivity.ontology.location.pit.Pit` are independent,
    independently serializable entities; ``Relationship`` is the explicit
    edge connecting them, deliberately not an object-graph pointer (see
    the design specification's AD-ON-02).

    Examples
    --------
    >>> edge = Relationship(source_id="bench-7", kind=RelationshipKind.BELONGS_TO, target_id="pit-west")
    >>> edge.kind
    <RelationshipKind.BELONGS_TO: 'belongs_to'>
    """

    source_id: str
    kind: RelationshipKind
    target_id: str

    def validate(self) -> None:
        if not self.source_id.strip():
            raise RelationshipError("Relationship.source_id must not be empty")
        if not self.target_id.strip():
            raise RelationshipError("Relationship.target_id must not be empty")
