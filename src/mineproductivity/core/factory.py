"""``BaseFactory``: encapsulates the "how" of constructing complex objects,
separate from the objects themselves.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from mineproductivity.core.result import Result

__all__ = ["BaseFactory"]

T = TypeVar("T")


class BaseFactory(ABC, Generic[T]):
    """Encapsulates the construction of an object of type ``T``.

    Prefer a factory over a constructor or classmethod when construction
    requires coordinating multiple inputs, choosing between alternative
    implementations, or enforcing invariants that depend on more than a
    single value object's own fields.

    Examples
    --------
    >>> class GreetingFactory(BaseFactory[str]):
    ...     def create(self, **kwargs: object) -> str:
    ...         name = kwargs.get("name", "world")
    ...         return f"Hello, {name}!"
    >>> GreetingFactory().create(name="MineProductivity")
    'Hello, MineProductivity!'
    >>> GreetingFactory().create_result(name="core").is_ok
    True
    """

    @abstractmethod
    def create(self, **kwargs: Any) -> T:
        """Construct and return a new instance of ``T``."""

    def create_result(self, **kwargs: Any) -> Result[T]:
        """Like :meth:`create`, but captures any exception as an ``Err``
        instead of raising."""
        try:
            return Result.ok(self.create(**kwargs))
        except Exception as exc:  # noqa: BLE001 - intentional error-boundary capture
            return Result.err(exc)
