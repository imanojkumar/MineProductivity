"""Tests for mineproductivity.ontology.quality.grade."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.quality.grade import GradeAttribute, QualitySpecification


class TestGradeAttribute:
    def test_valid_construction(self) -> None:
        grade = GradeAttribute(id="head-grade-cu", commodity_code="copper", unit="% Cu")
        assert grade.unit == "% Cu"

    def test_supported_kpis(self) -> None:
        assert GradeAttribute.meta.supported_kpis == ("QUAL.Recovery", "GRADE.HeadGrade")

    def test_empty_commodity_code_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            GradeAttribute(id="x", commodity_code="", unit="% Cu")

    def test_empty_unit_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            GradeAttribute(id="x", commodity_code="copper", unit="")


class TestQualitySpecification:
    def test_valid_construction(self) -> None:
        spec = QualitySpecification(
            id="spec-1", grade_attribute_code="head-grade-cu", min_value=0.3, max_value=1.2
        )
        assert spec.min_value == 0.3
        assert spec.max_value == 1.2

    def test_min_and_max_default_to_none(self) -> None:
        spec = QualitySpecification(id="spec-2", grade_attribute_code="head-grade-cu")
        assert spec.min_value is None
        assert spec.max_value is None

    def test_empty_grade_attribute_code_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            QualitySpecification(id="x", grade_attribute_code="")

    def test_min_greater_than_max_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            QualitySpecification(
                id="x", grade_attribute_code="head-grade-cu", min_value=2.0, max_value=1.0
            )

    def test_min_equal_max_accepted(self) -> None:
        spec = QualitySpecification(
            id="x", grade_attribute_code="head-grade-cu", min_value=1.0, max_value=1.0
        )
        assert spec.min_value == spec.max_value

    def test_only_min_set_accepted(self) -> None:
        spec = QualitySpecification(id="x", grade_attribute_code="head-grade-cu", min_value=0.5)
        assert spec.max_value is None
