"""Tests for mineproductivity.simulation.discrete_event.

Interface-only ABC contract tests (design spec §14, §35's
interface-purity proof).
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import mineproductivity.simulation.discrete_event as discrete_event_module
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.discrete_event import DiscreteEventModel
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            DiscreteEventModel()  # type: ignore[abstract]

    def test_advance_is_the_one_abstract_method(self) -> None:
        assert DiscreteEventModel.__abstractmethods__ == frozenset({"_advance"})

    def test_a_test_local_concrete_subclass_returns_state_and_delta(self) -> None:
        class _Queue(DiscreteEventModel):
            meta = SimulationMetadata(
                code="DISCRETEEVENT.TestQueueContract",
                category=SimulationCategory.DISCRETE_EVENT,
                description="Advances a queue by one event.",
            )

            def _advance(
                self, state: SimulationState, *, context: SimulationContext
            ) -> tuple[SimulationState, timedelta]:
                served = int(state.attributes.get("served", 0)) + 1
                return (
                    SimulationState(
                        attributes={"served": served}, simulated_time=state.simulated_time
                    ),
                    timedelta(minutes=10),
                )

        class _FakeStore: ...

        state = SimulationState(attributes={"served": 0}, simulated_time=_EPOCH)
        next_state, delta = _Queue()._advance(
            state, context=SimulationContext(event_store=_FakeStore())
        )
        assert next_state.attributes["served"] == 1
        assert delta == timedelta(minutes=10)

    def test_namespace_conformance_is_enforced_at_definition_time(self) -> None:
        with pytest.raises(SimulationValidationError, match="DISCRETEEVENT"):

            class _Wrong(DiscreteEventModel):
                meta = SimulationMetadata(
                    code="MONTECARLO.Wrong",
                    category=SimulationCategory.DISCRETE_EVENT,
                    description="x",
                )

                def _advance(
                    self, state: SimulationState, *, context: SimulationContext
                ) -> tuple[SimulationState, timedelta]:
                    return state, timedelta(minutes=1)


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(discrete_event_module, inspect.isclass):
            if issubclass(obj, DiscreteEventModel):
                assert inspect.isabstract(obj), f"{obj.__name__} is a concrete subclass"

    def test_no_package_module_subclasses_discrete_event_model(self) -> None:
        package_dir = Path(discrete_event_module.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "discrete_event.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = {
                        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                        for base in node.bases
                    }
                    assert "DiscreteEventModel" not in bases
