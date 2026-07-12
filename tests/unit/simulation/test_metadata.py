"""Tests for mineproductivity.simulation.metadata."""

from __future__ import annotations

import pytest

from mineproductivity.core import BaseMetadata
from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata


def _meta(code: str = "MONTECARLO.HaulCycleVariability", **overrides: object) -> SimulationMetadata:
    fields: dict[str, object] = {
        "code": code,
        "category": SimulationCategory.MONTE_CARLO,
        "description": "x",
    }
    fields.update(overrides)
    return SimulationMetadata(**fields)  # type: ignore[arg-type]


class TestSimulationCategory:
    def test_exactly_the_four_members_of_design_spec_29(self) -> None:
        assert {member.value for member in SimulationCategory} == {
            "monte_carlo",
            "discrete_event",
            "system_dynamics",
            "calibration",
        }


class TestSimulationMetadata:
    def test_subclasses_base_metadata(self) -> None:
        assert issubclass(SimulationMetadata, BaseMetadata)

    def test_minimal_valid_construction(self) -> None:
        meta = _meta()
        assert meta.code == "MONTECARLO.HaulCycleVariability"
        assert meta.category is SimulationCategory.MONTE_CARLO
        assert meta.version == "1.0.0"

    def test_name_defaults_to_code(self) -> None:
        assert _meta().name == "MONTECARLO.HaulCycleVariability"

    def test_explicit_name_is_preserved(self) -> None:
        assert _meta(name="Haul-cycle variability").name == "Haul-cycle variability"

    def test_empty_code_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="code must not be empty"):
            _meta(code="   ")

    def test_non_category_member_raises(self) -> None:
        with pytest.raises(SimulationValidationError, match="must be a SimulationCategory member"):
            _meta(category="monte_carlo")

    def test_replace_reruns_validation(self) -> None:
        with pytest.raises(SimulationValidationError):
            _meta().replace(code="")

    def test_code_names_a_type_never_a_run(self) -> None:
        """Design spec §29: the same code is shared by every run the
        model produces; a run's own identity is ``SimulationRun.id``."""
        assert _meta(version="2.1.0").version == "2.1.0"
