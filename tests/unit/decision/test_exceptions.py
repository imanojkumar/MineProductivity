"""Tests for mineproductivity.decision.exceptions."""

from __future__ import annotations

import pytest

from mineproductivity.core import NotFoundError, ValidationError
from mineproductivity.registry import RegistrationError

from mineproductivity.decision.exceptions import (
    DecisionModelNotFoundError,
    DecisionValidationError,
    DecisionVersionConflictError,
    NoApplicablePolicyError,
    PolicyConflictError,
)


class TestExceptionHierarchy:
    def test_decision_validation_error_is_a_validation_error(self) -> None:
        assert issubclass(DecisionValidationError, ValidationError)

    def test_no_applicable_policy_error_is_a_not_found_error(self) -> None:
        assert issubclass(NoApplicablePolicyError, NotFoundError)

    def test_decision_model_not_found_error_is_a_not_found_error(self) -> None:
        assert issubclass(DecisionModelNotFoundError, NotFoundError)

    def test_decision_version_conflict_error_is_a_registration_error(self) -> None:
        assert issubclass(DecisionVersionConflictError, RegistrationError)

    def test_policy_conflict_error_is_a_registration_error(self) -> None:
        assert issubclass(PolicyConflictError, RegistrationError)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            DecisionValidationError,
            NoApplicablePolicyError,
            DecisionModelNotFoundError,
            DecisionVersionConflictError,
            PolicyConflictError,
        ],
    )
    def test_each_exception_is_raisable_with_a_message(self, exc_cls: type[Exception]) -> None:
        with pytest.raises(exc_cls, match="boom"):
            raise exc_cls("boom")
