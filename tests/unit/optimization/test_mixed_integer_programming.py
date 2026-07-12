"""Tests for mineproductivity.optimization.mixed_integer_programming
(interface-only ABC contract, design spec §12, §35). Goal programming
is proven here as a problem-authoring pattern, never a category."""

from __future__ import annotations

import inspect

import pytest

import mineproductivity.optimization.mixed_integer_programming as mip_module
from mineproductivity.optimization.mixed_integer_programming import (
    MixedIntegerProgrammingModel,
)
from mineproductivity.optimization.problem import (
    Constraint,
    ConstraintOperator,
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    VariableDomain,
)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            MixedIntegerProgrammingModel()  # type: ignore[abstract]

    def test_solve_mip_is_the_one_abstract_method(self) -> None:
        assert MixedIntegerProgrammingModel.__abstractmethods__ == frozenset({"_solve_mip"})


class TestGoalProgrammingIsAnAuthoringPattern:
    def test_deviation_variables_and_goal_levels_are_ordinary_problem_parts(self) -> None:
        """Design spec §12: goal programming needs no separate
        category or ABC -- deviations are plain DecisionVariables and
        goal levels plain Constraints on a MIP-category problem."""
        problem = OptimizationProblem(
            code="GOAL.ProductionTarget",
            model_code="MIP.GoalSolver",
            objectives=(Objective(name="total_deviation", direction=ObjectiveDirection.MINIMIZE),),
            constraints=(
                Constraint(
                    name="tonnes_goal",
                    expression="tonnes + under_dev - over_dev",
                    operator=ConstraintOperator.EQUAL,
                    bound=50_000.0,
                ),
            ),
            variables=(
                DecisionVariable(name="tonnes", domain=VariableDomain.CONTINUOUS),
                DecisionVariable(
                    name="under_dev", domain=VariableDomain.CONTINUOUS, lower_bound=0.0
                ),
                DecisionVariable(
                    name="over_dev", domain=VariableDomain.CONTINUOUS, lower_bound=0.0
                ),
            ),
        )
        assert len(problem.variables) == 3  # an ordinary OptimizationProblem


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(mip_module, inspect.isclass):
            if issubclass(obj, MixedIntegerProgrammingModel):
                assert inspect.isabstract(obj)
