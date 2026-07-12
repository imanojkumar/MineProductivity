"""Tests for mineproductivity.optimization.exceptions."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.optimization.exceptions import (
    OptimizationExecutionError,
    OptimizationRunNotFoundError,
    OptimizationValidationError,
    OptimizationVersionConflictError,
    ProblemConflictError,
)
from mineproductivity.registry import RegistrationError


class TestHierarchy:
    def test_matches_the_core_and_registry_bases(self) -> None:
        assert issubclass(OptimizationValidationError, ValidationError)
        assert issubclass(OptimizationRunNotFoundError, NotFoundError)
        assert issubclass(OptimizationExecutionError, MineProductivityError)
        assert issubclass(OptimizationVersionConflictError, RegistrationError)
        assert issubclass(ProblemConflictError, RegistrationError)

    def test_all_are_mineproductivity_errors(self) -> None:
        for exception_type in (
            OptimizationValidationError,
            OptimizationRunNotFoundError,
            OptimizationExecutionError,
            OptimizationVersionConflictError,
            ProblemConflictError,
        ):
            assert issubclass(exception_type, MineProductivityError)
