"""Tests for mineproductivity.analytics.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

from mineproductivity.analytics.exceptions import (
    AnalyticsModelNotFoundError,
    AnalyticsValidationError,
    AnalyticsVersionConflictError,
    InsufficientDataError,
)


class TestExceptionHierarchy:
    def test_analytics_validation_error_is_a_validation_error(self) -> None:
        assert issubclass(AnalyticsValidationError, ValidationError)

    def test_insufficient_data_error_is_a_validation_error(self) -> None:
        assert issubclass(InsufficientDataError, ValidationError)

    def test_analytics_model_not_found_error_is_a_not_found_error(self) -> None:
        assert issubclass(AnalyticsModelNotFoundError, NotFoundError)

    def test_analytics_version_conflict_error_is_a_registration_error(self) -> None:
        assert issubclass(AnalyticsVersionConflictError, RegistrationError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            AnalyticsValidationError,
            InsufficientDataError,
            AnalyticsModelNotFoundError,
            AnalyticsVersionConflictError,
        ],
    )
    def test_each_exception_is_raisable_with_a_message(self, exc_cls: type[Exception]) -> None:
        with pytest.raises(exc_cls, match="boom"):
            raise exc_cls("boom")
