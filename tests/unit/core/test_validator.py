"""Tests for mineproductivity.core.validator."""

from __future__ import annotations

import pytest

from mineproductivity.core.exceptions import ValidationError
from mineproductivity.core.validator import BaseValidator, CompositeValidator, ValidationResult


class NotEmpty(BaseValidator[str]):
    def validate(self, candidate: str) -> ValidationResult:
        if candidate:
            return ValidationResult.success()
        return ValidationResult.failure("must not be empty")


class MaxLength(BaseValidator[str]):
    def validate(self, candidate: str) -> ValidationResult:
        if len(candidate) <= 3:
            return ValidationResult.success()
        return ValidationResult.failure("too long")


class TestValidationResult:
    def test_success_is_valid(self) -> None:
        assert ValidationResult.success().is_valid is True
        assert bool(ValidationResult.success()) is True

    def test_failure_is_invalid(self) -> None:
        result = ValidationResult.failure("bad")
        assert result.is_valid is False
        assert result.errors == ("bad",)

    def test_failure_accepts_multiple_errors(self) -> None:
        result = ValidationResult.failure("a", "b")
        assert result.errors == ("a", "b")

    def test_merge_combines_errors(self) -> None:
        merged = ValidationResult.failure("a").merge(ValidationResult.failure("b"))
        assert merged.errors == ("a", "b")

    def test_merge_success_with_success_stays_valid(self) -> None:
        merged = ValidationResult.success().merge(ValidationResult.success())
        assert merged.is_valid is True

    def test_raise_if_invalid_raises_on_failure(self) -> None:
        with pytest.raises(ValidationError):
            ValidationResult.failure("bad").raise_if_invalid()

    def test_raise_if_invalid_noop_on_success(self) -> None:
        ValidationResult.success().raise_if_invalid()  # should not raise


class TestBaseValidator:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseValidator()  # type: ignore[abstract]

    def test_call_delegates_to_validate(self) -> None:
        validator = NotEmpty()
        assert validator("x").is_valid is True
        assert validator("").is_valid is False


class TestCompositeValidator:
    def test_merges_errors_from_all_validators(self) -> None:
        composite = CompositeValidator(NotEmpty(), MaxLength())
        result = composite.validate("abcd")
        assert result.errors == ("too long",)

    def test_valid_when_all_pass(self) -> None:
        composite = CompositeValidator(NotEmpty(), MaxLength())
        assert composite.validate("ab").is_valid is True

    def test_accumulates_multiple_failures(self) -> None:
        composite = CompositeValidator(NotEmpty(), MaxLength())
        result = composite.validate("")
        assert "must not be empty" in result.errors

    def test_empty_validator_list_is_always_valid(self) -> None:
        composite: CompositeValidator[str] = CompositeValidator()
        assert composite.validate("anything").is_valid is True
