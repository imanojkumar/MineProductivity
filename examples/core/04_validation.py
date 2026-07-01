"""BaseValidator + CompositeValidator: validation as a composable object,
separate from the object being validated.

Run: python examples/core/04_validation.py
"""

from __future__ import annotations

from mineproductivity.core import (
    BaseValidator,
    CompositeValidator,
    ValidationError,
    ValidationResult,
)


class NotEmpty(BaseValidator[str]):
    def validate(self, candidate: str) -> ValidationResult:
        if candidate.strip():
            return ValidationResult.success()
        return ValidationResult.failure("must not be empty")


class MaxLength(BaseValidator[str]):
    def __init__(self, limit: int) -> None:
        self._limit = limit

    def validate(self, candidate: str) -> ValidationResult:
        if len(candidate) <= self._limit:
            return ValidationResult.success()
        return ValidationResult.failure(f"must be at most {self._limit} characters")


class AlphanumericOnly(BaseValidator[str]):
    def validate(self, candidate: str) -> ValidationResult:
        if candidate.isalnum():
            return ValidationResult.success()
        return ValidationResult.failure("must contain only letters and digits")


def main() -> None:
    # Compose three independent rules without subclassing anything.
    asset_code_rules = CompositeValidator(NotEmpty(), MaxLength(8), AlphanumericOnly())

    for candidate in ["TRK001", "", "this-code-is-way-too-long-and-has-dashes"]:
        result = asset_code_rules.validate(candidate)
        label = repr(candidate) if candidate else "'' (empty)"
        if result.is_valid:
            print(f"{label}: valid")
        else:
            print(f"{label}: invalid -> {list(result.errors)}")

    print()
    print("--- raise_if_invalid() for exception-based call sites ---")
    try:
        asset_code_rules.validate("bad code!").raise_if_invalid()
    except ValidationError as exc:
        print(f"raised: {exc!r}")


if __name__ == "__main__":
    main()
