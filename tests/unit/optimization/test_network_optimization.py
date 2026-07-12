"""Tests for mineproductivity.optimization.network_optimization
(interface-only ABC contract, design spec §16, §35)."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.optimization.network_optimization as net_module
from mineproductivity.optimization.network_optimization import NetworkOptimizationModel
from mineproductivity.optimization.problem import (
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    VariableDomain,
)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            NetworkOptimizationModel()  # type: ignore[abstract]

    def test_solve_network_is_the_one_abstract_method(self) -> None:
        assert NetworkOptimizationModel.__abstractmethods__ == frozenset({"_solve_network"})


class TestGraphStructureLivesInParameters:
    def test_no_node_or_edge_value_object_exists(self) -> None:
        """Design spec §16: the graph is carried in
        ``OptimizationProblem.parameters``."""
        import mineproductivity.optimization as optimization

        assert not hasattr(optimization, "Node")
        assert not hasattr(optimization, "Edge")
        problem = OptimizationProblem(
            code="NET.HaulRouting",
            model_code="NETWORK.MinCostFlow",
            objectives=(Objective(name="cost", direction=ObjectiveDirection.MINIMIZE),),
            variables=(DecisionVariable(name="flow_a_b", domain=VariableDomain.CONTINUOUS),),
            parameters={"edges": [["pit_a", "crusher", 12.5]]},
        )
        assert problem.parameters["edges"] == [["pit_a", "crusher", 12.5]]


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(net_module, inspect.isclass):
            if issubclass(obj, NetworkOptimizationModel):
                assert inspect.isabstract(obj)
