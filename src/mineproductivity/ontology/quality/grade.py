"""``GradeAttribute`` and ``QualitySpecification``: assay/grade reference entities."""

from __future__ import annotations

import dataclasses
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["GradeAttribute", "QualitySpecification"]


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class GradeAttribute(BaseEntityType):
    """A measurable grade/quality attribute for one commodity (e.g. "% Cu",
    "g/t Au").

    Examples
    --------
    >>> grade = GradeAttribute(id="head-grade-cu", commodity_code="copper", unit="% Cu")
    >>> grade.unit
    '% Cu'
    """

    code: ClassVar[str] = "GRADE_ATTRIBUTE"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Grade Attribute",
        description="A measurable grade/quality attribute for one commodity.",
        supported_kpis=("QUAL.Recovery", "GRADE.HeadGrade"),
    )

    commodity_code: str
    unit: str  # "% Cu", "g/t Au", ...

    def validate(self) -> None:
        if not self.commodity_code.strip():
            raise OntologyValidationError("GradeAttribute.commodity_code must not be empty")
        if not self.unit.strip():
            raise OntologyValidationError("GradeAttribute.unit must not be empty")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class QualitySpecification(BaseEntityType):
    """A governed acceptable range for one :class:`GradeAttribute`."""

    code: ClassVar[str] = "QUALITY_SPECIFICATION"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Quality Specification",
        description="A governed acceptable range for one grade attribute.",
    )

    grade_attribute_code: str
    min_value: float | None = dataclasses.field(default=None, kw_only=True)
    max_value: float | None = dataclasses.field(default=None, kw_only=True)

    def validate(self) -> None:
        if not self.grade_attribute_code.strip():
            raise OntologyValidationError(
                "QualitySpecification.grade_attribute_code must not be empty"
            )
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise OntologyValidationError("QualitySpecification.min_value must be <= max_value")
