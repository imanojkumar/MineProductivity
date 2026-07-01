"""``BaseValidator``: a pluggable, composable validation contract, decoupled
from the objects it validates (validation-as-object rather than
validation-as-method).
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from mineproductivity.core.exceptions import ValidationError

__all__ = ["BaseValidator", "CompositeValidator", "ValidationResult"]

T = TypeVar("T")


@dataclasses.dataclass(frozen=True, slots=True)
class ValidationResult:
    """The outcome of running a :class:`BaseValidator` over a candidate.

    Examples
    --------
    >>> ValidationResult.success().is_valid
    True
    >>> ValidationResult.failure("too short", "missing field").is_valid
    False
    """

    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Whether validation produced zero errors."""
        return not self.errors

    @classmethod
    def success(cls) -> ValidationResult:
        """Construct a result with no errors."""
        return cls()

    @classmethod
    def failure(cls, *errors: str) -> ValidationResult:
        """Construct a result carrying one or more error messages."""
        return cls(errors=tuple(errors))

    def merge(self, other: ValidationResult) -> ValidationResult:
        """Combine two results, accumulating errors from both."""
        return ValidationResult(errors=self.errors + other.errors)

    def raise_if_invalid(self) -> None:
        """Raise :class:`~mineproductivity.core.exceptions.ValidationError`
        if :attr:`is_valid` is ``False``."""
        if not self.is_valid:
            raise ValidationError(
                f"Validation failed with {len(self.errors)} error(s).",
                details={"errors": self.errors},
            )

    def __bool__(self) -> bool:
        return self.is_valid


class BaseValidator(ABC, Generic[T]):
    """A standalone object that knows how to validate a candidate of type ``T``.

    Separating validation from the object being validated follows the
    Single Responsibility Principle: a value object enforces its own
    *invariants* in ``validate()``/``_normalize()``
    (see :class:`~mineproductivity.core.value_object.BaseValueObject`),
    while a ``BaseValidator`` enforces *contextual* business rules that
    may depend on external state (a database lookup, another aggregate, a
    configuration flag) and that may differ by use case.
    """

    @abstractmethod
    def validate(self, candidate: T) -> ValidationResult:
        """Validate ``candidate`` and return the accumulated result."""

    def __call__(self, candidate: T) -> ValidationResult:
        return self.validate(candidate)


class CompositeValidator(BaseValidator[T]):
    """Combines multiple validators into one, merging all of their errors.

    Demonstrates composition over inheritance: instead of subclassing to
    add a rule, wrap additional :class:`BaseValidator` instances.

    Examples
    --------
    >>> class NotEmpty(BaseValidator[str]):
    ...     def validate(self, candidate: str) -> ValidationResult:
    ...         return (
    ...             ValidationResult.success()
    ...             if candidate
    ...             else ValidationResult.failure("must not be empty")
    ...         )
    >>> class MaxLength(BaseValidator[str]):
    ...     def validate(self, candidate: str) -> ValidationResult:
    ...         return (
    ...             ValidationResult.success()
    ...             if len(candidate) <= 3
    ...             else ValidationResult.failure("too long")
    ...         )
    >>> CompositeValidator(NotEmpty(), MaxLength()).validate("abcd").errors
    ('too long',)
    """

    def __init__(self, *validators: BaseValidator[T]) -> None:
        self._validators = validators

    def validate(self, candidate: T) -> ValidationResult:
        result = ValidationResult.success()
        for validator in self._validators:
            result = result.merge(validator.validate(candidate))
        return result
