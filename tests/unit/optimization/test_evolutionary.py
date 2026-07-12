"""Tests for mineproductivity.optimization.evolutionary
(interface-only ABC contract plus seed-anchored reproducibility,
design spec §15, §33, §35)."""

from __future__ import annotations

import inspect
import random

import pytest

import mineproductivity.optimization.evolutionary as evo_module
from mineproductivity.optimization.abstractions import OptimizationContext
from mineproductivity.optimization.evolutionary import EvolutionaryMetaheuristicModel
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.problem import (
    DecisionVariable,
    Objective,
    ObjectiveDirection,
    OptimizationProblem,
    VariableDomain,
)
from mineproductivity.optimization.state import OptimizationState


class _SeededWalk(EvolutionaryMetaheuristicModel):
    """Test-local: each iteration derives its randomness solely from
    the seed carried in state attributes -- never internal generator
    state (design spec §33, §34)."""

    meta = OptimizationMetadata(
        code="EVOLUTIONARY.TestSeededWalk",
        category=OptimizationCategory.EVOLUTIONARY_METAHEURISTIC,
        description="Seed-anchored random walk over the incumbent.",
    )

    def _iterate(
        self,
        problem: OptimizationProblem,
        state: OptimizationState,
        *,
        context: OptimizationContext,
    ) -> OptimizationState:
        step = int(state.attributes.get("step", 0))
        seed = int(problem.parameters.get("seed", 0))
        rng = random.Random(seed * 1_000_003 + step)
        incumbent = float(state.attributes.get("incumbent", 0.0)) + rng.uniform(0.0, 1.0)
        return OptimizationState(attributes={"step": step + 1, "incumbent": incumbent})


def _problem(seed: int = 7) -> OptimizationProblem:
    return OptimizationProblem(
        code="TEST.EvoWalk",
        model_code=_SeededWalk.meta.code,
        objectives=(Objective(name="incumbent", direction=ObjectiveDirection.MAXIMIZE),),
        variables=(DecisionVariable(name="x", domain=VariableDomain.CONTINUOUS),),
        parameters={"seed": seed},
    )


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises(self) -> None:
        with pytest.raises(TypeError):
            EvolutionaryMetaheuristicModel()  # type: ignore[abstract]

    def test_iterate_is_the_one_abstract_method(self) -> None:
        assert EvolutionaryMetaheuristicModel.__abstractmethods__ == frozenset({"_iterate"})


class TestReproducibility:
    def test_identical_seeds_produce_identical_trajectories(self) -> None:
        """Design spec §35: independent of execution order."""
        model = _SeededWalk()
        context = OptimizationContext()
        start = OptimizationState(attributes={"step": 0, "incumbent": 0.0})

        def trajectory(seed: int) -> list[float]:
            state = start
            values: list[float] = []
            for _ in range(5):
                state = model._iterate(_problem(seed), state, context=context)
                values.append(float(state.attributes["incumbent"]))
            return values

        first = trajectory(7)
        trajectory(999)  # interleaved run must not perturb anything
        assert trajectory(7) == first
        assert trajectory(8) != first
        assert vars(model) == {}  # stateless (design spec §29, §32)


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(evo_module, inspect.isclass):
            if issubclass(obj, EvolutionaryMetaheuristicModel):
                assert inspect.isabstract(obj)
