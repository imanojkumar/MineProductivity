"""Tests for mineproductivity.simulation.calibration.

Interface-only ABC contract tests (design spec §16, §35's
interface-purity proof).
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

import mineproductivity.simulation.calibration as calibration_module
from mineproductivity.digital_twin import TwinSnapshot, TwinState, TwinStatus
from mineproductivity.events import AsOf
from mineproductivity.simulation.abstractions import SimulationContext, SimulationModel
from mineproductivity.simulation.calibration import CalibrationModel

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class TestInterfaceOnlyContract:
    def test_bare_abc_instantiation_raises_type_error(self) -> None:
        with pytest.raises(TypeError):
            CalibrationModel()  # type: ignore[abstract]

    def test_calibrate_is_the_one_abstract_method(self) -> None:
        assert CalibrationModel.__abstractmethods__ == frozenset({"_calibrate"})

    def test_calibration_model_is_not_a_simulation_model(self) -> None:
        """Design spec §8: calibration is conceptually distinct from
        running a model forward -- never forced under the same root."""
        assert not issubclass(CalibrationModel, SimulationModel)

    def test_ground_truth_is_a_sequence_of_twin_snapshots(self) -> None:
        class _Echo(CalibrationModel):
            def _calibrate(
                self,
                model_code: str,
                ground_truth: Sequence[TwinSnapshot],
                *,
                context: SimulationContext,
            ) -> Mapping[str, Any]:
                return {"observations": len(ground_truth)}

        class _FakeStore: ...

        snapshot = TwinSnapshot(
            twin_id="FLEET-NORTH",
            state=TwinState(attributes={"trucks": 24}, captured_at=_EPOCH),
            status=TwinStatus.SYNCHRONIZED,
            as_of=AsOf(utc=_EPOCH),
        )
        fitted = _Echo()._calibrate(
            "MONTECARLO.HaulCycleVariability",
            [snapshot],
            context=SimulationContext(event_store=_FakeStore()),
        )
        assert fitted == {"observations": 1}


class TestInterfacePurityProof:
    def test_module_defines_no_concrete_subclass(self) -> None:
        for _, obj in inspect.getmembers(calibration_module, inspect.isclass):
            if issubclass(obj, CalibrationModel):
                assert inspect.isabstract(obj), f"{obj.__name__} is a concrete subclass"

    def test_no_package_module_subclasses_calibration_model(self) -> None:
        package_dir = Path(calibration_module.__file__).parent
        for py_file in package_dir.glob("*.py"):
            if py_file.name == "calibration.py":
                continue
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = {
                        base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
                        for base in node.bases
                    }
                    assert "CalibrationModel" not in bases
