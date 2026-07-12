"""Tests for mineproductivity.simulation.exceptions."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError
from mineproductivity.simulation.exceptions import (
    ScenarioConflictError,
    SimulationExecutionError,
    SimulationRunNotFoundError,
    SimulationValidationError,
    SimulationVersionConflictError,
)


class TestHierarchy:
    """Design spec §6: each exception subclasses the matching ``core``
    (or ``registry``) exception, exactly as every other domain
    package's exceptions do."""

    def test_simulation_validation_error(self) -> None:
        assert issubclass(SimulationValidationError, ValidationError)

    def test_simulation_run_not_found_error(self) -> None:
        assert issubclass(SimulationRunNotFoundError, NotFoundError)

    def test_simulation_execution_error(self) -> None:
        assert issubclass(SimulationExecutionError, MineProductivityError)

    def test_simulation_version_conflict_error(self) -> None:
        assert issubclass(SimulationVersionConflictError, RegistrationError)

    def test_scenario_conflict_error(self) -> None:
        assert issubclass(ScenarioConflictError, RegistrationError)

    def test_all_are_mineproductivity_errors(self) -> None:
        for exception_type in (
            SimulationValidationError,
            SimulationRunNotFoundError,
            SimulationExecutionError,
            SimulationVersionConflictError,
            ScenarioConflictError,
        ):
            assert issubclass(exception_type, MineProductivityError)
