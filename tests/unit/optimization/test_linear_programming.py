"""Tests for mineproductivity.optimization.linear_programming
(interface-only ABC contract, design spec §11, §35)."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.optimization.linear_programming as lp_module
from mineproductivity.optimization.exceptions import OptimizationValidationError
from mineproductivity.optimization.linear_programming import LinearProgrammingModel
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            LinearProgrammingModel()  # type: ignore[abstract]

    def test_solve_lp_is_the_one_abstract_method(self) -> None:
        assert LinearProgrammingModel.__abstractmethods__ == frozenset({"_solve_lp"})

    def test_namespace_conformance_enforced_at_definition_time(self) -> None:
        with pytest.raises(OptimizationValidationError, match="'LP'"):

            class _Wrong(LinearProgrammingModel):  # type: ignore[abstract]
                meta = OptimizationMetadata(
                    code="MIP.Wrong",
                    category=OptimizationCategory.LINEAR_PROGRAMMING,
                    description="x",
                )

    def test_category_conformance_enforced_at_definition_time(self) -> None:
        with pytest.raises(OptimizationValidationError, match="meta.category must be"):

            class _Wrong(LinearProgrammingModel):  # type: ignore[abstract]
                meta = OptimizationMetadata(
                    code="LP.WrongCategory",
                    category=OptimizationCategory.CONSTRAINT_PROGRAMMING,
                    description="x",
                )


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(lp_module, inspect.isclass):
            if issubclass(obj, LinearProgrammingModel):
                assert inspect.isabstract(obj)
