"""Tests for mineproductivity.optimization.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import BaseMetadata
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata


def _meta(code: str = "MIP.FleetAllocation", **overrides: object) -> OptimizationMetadata:
    fields: dict[str, object] = {
        "code": code,
        "category": OptimizationCategory.MIXED_INTEGER_PROGRAMMING,
        "description": "x",
    }
    fields.update(overrides)
    return OptimizationMetadata(**fields)  # type: ignore[arg-type]


class TestOptimizationCategory:
    def test_exactly_the_six_members_of_design_spec_29(self) -> None:
        assert {member.value for member in OptimizationCategory} == {
            "linear_programming",
            "mixed_integer_programming",
            "constraint_programming",
            "multi_objective",
            "evolutionary_metaheuristic",
            "network_optimization",
        }


class TestOptimizationMetadata:
    def test_subclasses_base_metadata_with_name_defaulting_to_code(self) -> None:
        assert issubclass(OptimizationMetadata, BaseMetadata)
        assert _meta().name == "MIP.FleetAllocation"
        assert _meta().version == "1.0.0"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(OptimizationValidationError, match="code must not be empty"):
            _meta(code="  ")

    def test_non_category_member_raises(self) -> None:
        with pytest.raises(OptimizationValidationError, match="OptimizationCategory member"):
            _meta(category="mip")

    def test_replace_reruns_validation(self) -> None:
        with pytest.raises(OptimizationValidationError):
            _meta().replace(code="")
