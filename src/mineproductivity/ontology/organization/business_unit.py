"""``BusinessUnit`` and ``Contractor``: the enterprise/ownership hierarchy."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["BusinessUnit", "Contractor"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class BusinessUnit(BaseEntityType):
    """An enterprise business unit that one or more mines roll up to --
    the scope :class:`~mineproductivity.ontology.cost.cost_center.CostCenter`
    and cross-site benchmarking (Cookbook Part I, Ch. 6) are computed
    against."""

    code: ClassVar[str] = "BUSINESS_UNIT"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Business Unit",
        description="An enterprise business unit that one or more mines roll up to.",
    )

    parent_business_unit_id: str | None = dataclasses.field(default=None, kw_only=True)


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Contractor(BaseEntityType):
    """A third-party contractor providing equipment, labour, or services."""

    code: ClassVar[str] = "CONTRACTOR"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Contractor",
        description="A third-party contractor providing equipment, labour, or services.",
    )

    service_type: str = dataclasses.field(default="", kw_only=True)
