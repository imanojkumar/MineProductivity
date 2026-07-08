"""Tests for mineproductivity.digital_twin.simulation.

Interface-only ABC contract tests (design spec §14, §32's
interface-purity proof) -- no algorithmic-correctness test exists for
``TwinSimulationModel``, deliberately: this package ships zero concrete
subclasses, and choosing a simulation algorithm is exactly the scope
this package's charter excludes (ADR-0008).
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

import mineproductivity.digital_twin.simulation as simulation_module
from mineproductivity.digital_twin.abstractions import Twin
from mineproductivity.digital_twin.result import TwinSimulationResult
from mineproductivity.digital_twin.simulation import TwinSimulationModel
from mineproductivity.digital_twin.state import TwinState
from mineproductivity.events import AsOf

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            TwinSimulationModel()  # type: ignore[abstract]

    def test_simulate_is_the_one_abstract_method(self) -> None:
        assert TwinSimulationModel.__abstractmethods__ == frozenset({"_simulate"})

    def test_a_test_local_concrete_subclass_satisfies_the_contract(self) -> None:
        """The ABC is implementable -- the extension point a future
        ``simulation``/``optimization``/``agents`` plugin registers
        against (design spec §27.2)."""

        class _EchoSimulation(TwinSimulationModel):
            def _simulate(
                self, twin: Twin, hypothesis: Mapping[str, Any], *, as_of: AsOf
            ) -> TwinSimulationResult:
                return TwinSimulationResult(
                    twin_id=twin.id,
                    hypothesis=hypothesis,
                    predicted_state=TwinState(
                        attributes=dict(twin.state.attributes) | dict(hypothesis),
                        captured_at=_EPOCH,
                    ),
                )

        assert TwinSimulationModel.__abstractmethods__ <= set(dir(_EchoSimulation))


class TestInterfacePurityProof:
    """Design spec §32 proof 3: ``TwinSimulationModel`` has zero
    concrete, non-test subclasses anywhere in
    ``src/mineproductivity/digital_twin/``."""

    def test_simulation_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(simulation_module, inspect.isclass):
            if issubclass(obj, TwinSimulationModel):
                assert inspect.isabstract(obj), f"{obj.__name__} is a concrete subclass"

    def test_no_package_module_subclasses_twin_simulation_model(self) -> None:
        package_dir = Path(simulation_module.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "simulation.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    base_names = {
                        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                        for base in node.bases
                    }
                    assert "TwinSimulationModel" not in base_names, (
                        f"{py_file.name}:{node.name} subclasses TwinSimulationModel"
                    )
