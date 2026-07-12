"""Tests for mineproductivity.optimization.constraint_programming
(interface-only ABC contract, design spec §13, §35)."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.optimization.constraint_programming as cp_module
from mineproductivity.optimization.constraint_programming import ConstraintProgrammingModel


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            ConstraintProgrammingModel()  # type: ignore[abstract]

    def test_solve_cp_is_the_one_abstract_method(self) -> None:
        assert ConstraintProgrammingModel.__abstractmethods__ == frozenset({"_solve_cp"})


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(cp_module, inspect.isclass):
            if issubclass(obj, ConstraintProgrammingModel):
                assert inspect.isabstract(obj)
