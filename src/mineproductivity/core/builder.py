"""``BaseBuilder``: step-by-step, fluent construction of complex objects."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar

from mineproductivity.core.result import Result

__all__ = ["BaseBuilder"]

T = TypeVar("T")


class BaseBuilder(ABC, Generic[T]):
    """Fluent, step-by-step construction of an object of type ``T``.

    Prefer :class:`BaseBuilder` over
    :class:`~mineproductivity.core.factory.BaseFactory` when construction
    has many optional steps/parameters that read better as chained method
    calls than as a single call with many keyword arguments.

    Examples
    --------
    >>> class GreetingBuilder(BaseBuilder[str]):
    ...     def __init__(self) -> None:
    ...         self._name = "world"
    ...     def with_name(self, name: str) -> Self:
    ...         self._name = name
    ...         return self
    ...     def build(self) -> str:
    ...         return f"Hello, {self._name}!"
    >>> GreetingBuilder().with_name("MineProductivity").build()
    'Hello, MineProductivity!'
    """

    @abstractmethod
    def build(self) -> T:
        """Construct and return the final object. May raise on incomplete state."""

    def reset(self) -> Self:
        """Return the builder to its initial state so it can be reused.

        The default implementation is a no-op returning ``self``; override
        it if the builder accumulates mutable state that must be cleared
        between builds.
        """
        return self

    def build_result(self) -> Result[T]:
        """Like :meth:`build`, but captures any exception as an ``Err``
        instead of raising."""
        try:
            return Result.ok(self.build())
        except Exception as exc:  # noqa: BLE001 - intentional error-boundary capture
            return Result.err(exc)
