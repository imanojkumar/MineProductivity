"""Tests for mineproductivity.simulation.system_dynamics.

Interface-only ABC contract tests (design spec §15, §35's
interface-purity proof).
"""

from __future__ import annotations

import ast
import inspect
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import mineproductivity.simulation.system_dynamics as system_dynamics_module
from mineproductivity.simulation.abstractions import SimulationContext
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.state import SimulationState
from mineproductivity.simulation.system_dynamics import SystemDynamicsModel

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            SystemDynamicsModel()  # type: ignore[abstract]

    def test_step_is_the_one_abstract_method(self) -> None:
        assert SystemDynamicsModel.__abstractmethods__ == frozenset({"_step"})

    def test_a_test_local_concrete_subclass_steps_by_the_supplied_dt(self) -> None:
        class _Stock(SystemDynamicsModel):
            meta = SimulationMetadata(
                code="SYSTEMDYNAMICS.TestStockContract",
                category=SimulationCategory.SYSTEM_DYNAMICS,
                description="Accumulates a constant inflow per step.",
            )

            def _step(
                self, state: SimulationState, *, context: SimulationContext, dt: timedelta
            ) -> SimulationState:
                level = float(state.attributes["level"]) + dt.total_seconds() / 60.0
                return SimulationState(
                    attributes={"level": level}, simulated_time=state.simulated_time
                )

        class _FakeStore: ...

        state = SimulationState(attributes={"level": 0.0}, simulated_time=_EPOCH)
        stepped = _Stock()._step(
            state, context=SimulationContext(event_store=_FakeStore()), dt=timedelta(minutes=5)
        )
        assert stepped.attributes["level"] == 5.0

    def test_namespace_conformance_is_enforced_at_definition_time(self) -> None:
        with pytest.raises(SimulationValidationError, match="SYSTEMDYNAMICS"):

            class _Wrong(SystemDynamicsModel):
                meta = SimulationMetadata(
                    code="DISCRETEEVENT.Wrong",
                    category=SimulationCategory.SYSTEM_DYNAMICS,
                    description="x",
                )

                def _step(
                    self, state: SimulationState, *, context: SimulationContext, dt: timedelta
                ) -> SimulationState:
                    return state


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(system_dynamics_module, inspect.isclass):
            if issubclass(obj, SystemDynamicsModel):
                assert inspect.isabstract(obj), f"{obj.__name__} is a concrete subclass"

    def test_no_package_module_subclasses_system_dynamics_model(self) -> None:
        package_dir = Path(system_dynamics_module.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "system_dynamics.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = {
                        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                        for base in node.bases
                    }
                    assert "SystemDynamicsModel" not in bases
