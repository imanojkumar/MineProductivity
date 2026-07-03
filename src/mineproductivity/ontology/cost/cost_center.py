"""``CostCenter`` and ``CostCategory``: cost accounting reference entities."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["CostCategory", "CostCenter"]


class CostCategory(Enum):
    """The cost categories a :class:`CostCenter` can classify spend
    under, each mapping to a corresponding ``COST.*`` KPI namespace."""

    FUEL = "fuel"
    LABOUR = "labour"
    MAINTENANCE = "maintenance"
    CONSUMABLES = "consumables"
    OVERHEAD = "overhead"


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class CostCenter(BaseEntityType):
    """A cost center scoped to a
    :class:`~mineproductivity.ontology.organization.business_unit.BusinessUnit`.

    Examples
    --------
    >>> cc = CostCenter(id="CC-FUEL-01", business_unit_id="bu-1", category=CostCategory.FUEL)
    >>> cc.category
    <CostCategory.FUEL: 'fuel'>
    """

    code: ClassVar[str] = "COST_CENTER"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Cost Center",
        description="A cost center scoped to a business unit.",
        supported_kpis=("COST.CostPerTonne",),
    )

    business_unit_id: str
    category: CostCategory

    def validate(self) -> None:
        if not self.business_unit_id.strip():
            raise OntologyValidationError("CostCenter.business_unit_id must not be empty")
