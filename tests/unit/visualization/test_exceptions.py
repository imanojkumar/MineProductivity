"""Tests for mineproductivity.visualization.exceptions (design spec
§6, §30)."""

from __future__ import annotations

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError
from mineproductivity.visualization.exceptions import (
    DashboardNotFoundError,
    RenderingError,
    VisualizationValidationError,
    VisualizationVersionConflictError,
)


class TestHierarchy:
    def test_validation_error_subclasses_core_validation_error(self) -> None:
        assert issubclass(VisualizationValidationError, ValidationError)

    def test_dashboard_not_found_subclasses_core_not_found(self) -> None:
        assert issubclass(DashboardNotFoundError, NotFoundError)

    def test_rendering_error_subclasses_root(self) -> None:
        assert issubclass(RenderingError, MineProductivityError)

    def test_version_conflict_subclasses_registration_error(self) -> None:
        assert issubclass(VisualizationVersionConflictError, RegistrationError)

    def test_all_are_catchable_as_the_platform_root(self) -> None:
        for exc_type in (
            VisualizationValidationError,
            DashboardNotFoundError,
            RenderingError,
            VisualizationVersionConflictError,
        ):
            assert issubclass(exc_type, MineProductivityError)
