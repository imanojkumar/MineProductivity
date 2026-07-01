"""``BaseSpecification``: the Specification pattern for composable, reusable
business predicates.
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar

__all__ = [
    "AndSpecification",
    "BaseSpecification",
    "NotSpecification",
    "OrSpecification",
    "PredicateSpecification",
]

T = TypeVar("T")


class BaseSpecification(ABC, Generic[T]):
    """A composable predicate over candidates of type ``T``.

    A specification encapsulates a single business rule as an object,
    which can then be combined with ``&``, ``|``, and ``~`` to build up
    more complex rules without editing existing classes (Open/Closed
    Principle). Specifications can be reused anywhere a yes/no decision
    about a candidate is required -- most notably to filter
    :meth:`~mineproductivity.core.repository.BaseRepository.list` results.

    Examples
    --------
    >>> class IsPositive(BaseSpecification[int]):
    ...     def is_satisfied_by(self, candidate: int) -> bool:
    ...         return candidate > 0
    >>> class IsEven(BaseSpecification[int]):
    ...     def is_satisfied_by(self, candidate: int) -> bool:
    ...         return candidate % 2 == 0
    >>> spec = IsPositive() & IsEven()
    >>> spec.is_satisfied_by(4)
    True
    >>> spec.is_satisfied_by(-4)
    False
    >>> (~IsPositive()).is_satisfied_by(-1)
    True
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Return whether ``candidate`` satisfies this specification."""

    def __call__(self, candidate: T) -> bool:
        return self.is_satisfied_by(candidate)

    def __and__(self, other: BaseSpecification[T]) -> AndSpecification[T]:
        return AndSpecification(self, other)

    def __or__(self, other: BaseSpecification[T]) -> OrSpecification[T]:
        return OrSpecification(self, other)

    def __invert__(self) -> NotSpecification[T]:
        return NotSpecification(self)


@dataclasses.dataclass(frozen=True, slots=True)
class AndSpecification(BaseSpecification[T]):
    """A specification satisfied when both wrapped specifications are satisfied."""

    left: BaseSpecification[T]
    right: BaseSpecification[T]

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


@dataclasses.dataclass(frozen=True, slots=True)
class OrSpecification(BaseSpecification[T]):
    """A specification satisfied when either wrapped specification is satisfied."""

    left: BaseSpecification[T]
    right: BaseSpecification[T]

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


@dataclasses.dataclass(frozen=True, slots=True)
class NotSpecification(BaseSpecification[T]):
    """A specification satisfied when the wrapped specification is not."""

    wrapped: BaseSpecification[T]

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.wrapped.is_satisfied_by(candidate)


@dataclasses.dataclass(frozen=True, slots=True)
class PredicateSpecification(BaseSpecification[T]):
    """Adapts any plain callable into a :class:`BaseSpecification`.

    Useful for one-off specifications that do not warrant a dedicated
    class.

    Examples
    --------
    >>> adult = PredicateSpecification(lambda age: age >= 18)
    >>> adult.is_satisfied_by(21)
    True
    """

    predicate: Callable[[T], bool]

    def is_satisfied_by(self, candidate: T) -> bool:
        return self.predicate(candidate)
