"""``EmissionFactor`` and ``MonitoringPoint``: environmental reference entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["EmissionFactor", "MonitoringPoint"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class EmissionFactor(BaseEntityType):
    """A governed emission factor for one resource type (e.g. diesel,
    grid power), feeding ``CARBON.*`` KPIs.

    Examples
    --------
    >>> factor = EmissionFactor(id="diesel-factor", resource_type="diesel", kg_co2e_per_unit=2.68)
    >>> factor.kg_co2e_per_unit
    2.68
    """

    code: ClassVar[str] = "EMISSION_FACTOR"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Emission Factor",
        description="A governed emission factor for one resource type.",
        supported_kpis=("CARBON.CO2PerTonne",),
    )

    resource_type: str  # "diesel", "grid_power", ...
    kg_co2e_per_unit: float

    def validate(self) -> None:
        if not self.resource_type.strip():
            raise OntologyValidationError("EmissionFactor.resource_type must not be empty")
        if self.kg_co2e_per_unit < 0:
            raise OntologyValidationError("EmissionFactor.kg_co2e_per_unit must be >= 0")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class MonitoringPoint(BaseEntityType):
    """An environmental monitoring point (dust, noise, water quality, ...)."""

    code: ClassVar[str] = "MONITORING_POINT"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Monitoring Point",
        description="An environmental monitoring point.",
    )

    mine_id: str
    measurement_type: str  # "dust", "noise", "water_quality", ...

    def validate(self) -> None:
        if not self.measurement_type.strip():
            raise OntologyValidationError("MonitoringPoint.measurement_type must not be empty")
