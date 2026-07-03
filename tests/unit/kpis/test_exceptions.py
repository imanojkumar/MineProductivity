"""Tests for mineproductivity.kpis.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import MineProductivityError, NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

from mineproductivity.kpis.exceptions import (
    KPIAggregationError,
    KPICircularDependencyError,
    KPINotFoundError,
    KPIValidationError,
    KPIVersionConflictError,
)


class TestExceptionHierarchy:
    def test_kpi_validation_error_is_a_validation_error(self) -> None:
        assert issubclass(KPIValidationError, ValidationError)

    def test_kpi_not_found_error_is_a_not_found_error(self) -> None:
        assert issubclass(KPINotFoundError, NotFoundError)

    def test_kpi_circular_dependency_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(KPICircularDependencyError, MineProductivityError)

    def test_kpi_aggregation_error_is_a_mineproductivity_error(self) -> None:
        assert issubclass(KPIAggregationError, MineProductivityError)

    def test_kpi_version_conflict_error_is_a_registration_error(self) -> None:
        assert issubclass(KPIVersionConflictError, RegistrationError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            KPIValidationError,
            KPINotFoundError,
            KPICircularDependencyError,
            KPIAggregationError,
            KPIVersionConflictError,
        ],
    )
    def test_each_exception_is_raisable_with_a_message(self, exc_cls: type[Exception]) -> None:
        with pytest.raises(exc_cls, match="boom"):
            raise exc_cls("boom")
