"""Tests for mineproductivity.optimization.multi_objective
(interface-only ABC contract, design spec §14, §35)."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.optimization.multi_objective as mo_module
from mineproductivity.optimization.multi_objective import MultiObjectiveModel


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            MultiObjectiveModel()  # type: ignore[abstract]

    def test_solve_pareto_is_the_one_abstract_method(self) -> None:
        assert MultiObjectiveModel.__abstractmethods__ == frozenset({"_solve_pareto"})


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(mo_module, inspect.isclass):
            if issubclass(obj, MultiObjectiveModel):
                assert inspect.isabstract(obj)
