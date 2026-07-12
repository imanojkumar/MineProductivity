"""Tests for mineproductivity.simulation.montecarlo.

Interface-only ABC contract tests (design spec §13, §35's
interface-purity proof) -- no algorithmic-correctness test exists for
``MonteCarloModel``, deliberately.
"""

from __future__ import annotations

import ast
import inspect
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import mineproductivity.simulation.montecarlo as montecarlo_module
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.montecarlo import MonteCarloModel
from mineproductivity.simulation.result import SimulationResult
from mineproductivity.simulation.scenario import Scenario
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _SeededModel(MonteCarloModel):
    """Test-local concrete model: outcome is a pure function of the
    supplied seed -- the §33 reproducibility contract."""

    meta = SimulationMetadata(
        code="MONTECARLO.TestSeededContract",
        category=SimulationCategory.MONTE_CARLO,
        description="Outcome is a pure function of the supplied seed.",
    )

    def _trial(
        self, scenario: Scenario, *, context: SimulationContext, random_seed: int
    ) -> SimulationResult:
        outcome = random.Random(random_seed).uniform(0.0, 100.0)
        return SimulationResult(
            final_state=SimulationState(attributes={"outcome": outcome}, simulated_time=_EPOCH)
        )


class _FakeStore: ...


def _scenario() -> Scenario:
    return Scenario(
        code="TEST.MonteCarloContract",
        model_code=_SeededModel.meta.code,
        time_horizon=timedelta(hours=1),
    )


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            MonteCarloModel()  # type: ignore[abstract]

    def test_trial_is_the_one_abstract_method(self) -> None:
        assert MonteCarloModel.__abstractmethods__ == frozenset({"_trial"})

    def test_namespace_conformance_is_enforced_at_definition_time(self) -> None:
        with pytest.raises(SimulationValidationError, match="MONTECARLO"):

            class _Wrong(MonteCarloModel):
                meta = SimulationMetadata(
                    code="SYSTEMDYNAMICS.Wrong",
                    category=SimulationCategory.MONTE_CARLO,
                    description="x",
                )

                def _trial(
                    self, scenario: Scenario, *, context: SimulationContext, random_seed: int
                ) -> SimulationResult:
                    return SimulationResult()

    def test_category_conformance_is_enforced_at_definition_time(self) -> None:
        with pytest.raises(SimulationValidationError, match="meta.category must be"):

            class _Wrong(MonteCarloModel):
                meta = SimulationMetadata(
                    code="MONTECARLO.WrongCategory",
                    category=SimulationCategory.SYSTEM_DYNAMICS,
                    description="x",
                )

                def _trial(
                    self, scenario: Scenario, *, context: SimulationContext, random_seed: int
                ) -> SimulationResult:
                    return SimulationResult()


class TestReproducibility:
    """Design spec §35's reproducibility proof: identical seeds produce
    identical outputs; distinct seeds produce different ones."""

    def test_identical_seeds_produce_identical_results(self) -> None:
        model = _SeededModel()
        context = SimulationContext(event_store=_FakeStore())
        first = model._trial(_scenario(), context=context, random_seed=42)
        second = model._trial(_scenario(), context=context, random_seed=42)
        assert first.final_state == second.final_state

    def test_distinct_seeds_produce_distinct_results(self) -> None:
        model = _SeededModel()
        context = SimulationContext(event_store=_FakeStore())
        first = model._trial(_scenario(), context=context, random_seed=1)
        second = model._trial(_scenario(), context=context, random_seed=2)
        assert first.final_state != second.final_state

    def test_the_model_holds_no_mutable_generator_state_across_trials(self) -> None:
        """§34's recorded anti-pattern: all randomness derives from the
        supplied seed, so trial order cannot matter."""
        model = _SeededModel()
        context = SimulationContext(event_store=_FakeStore())
        before = model._trial(_scenario(), context=context, random_seed=7)
        model._trial(_scenario(), context=context, random_seed=999)  # interleaved trial
        after = model._trial(_scenario(), context=context, random_seed=7)
        assert before.final_state == after.final_state
        assert vars(model) == {}  # stateless: no instance attributes at all (§29)


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(montecarlo_module, inspect.isclass):
            if issubclass(obj, MonteCarloModel):
                assert inspect.isabstract(obj), f"{obj.__name__} is a concrete subclass"

    def test_no_package_module_subclasses_monte_carlo_model(self) -> None:
        package_dir = Path(montecarlo_module.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "montecarlo.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = {
                        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                        for base in node.bases
                    }
                    assert "MonteCarloModel" not in bases
