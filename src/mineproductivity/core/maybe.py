"""``Maybe[T]``: an explicit representation of an optional value, as an
alternative to using ``None`` (and losing the ability to distinguish
"no value" from "a value that happens to be ``None``").
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from mineproductivity.core.result import Result

__all__ = ["Maybe"]

T = TypeVar("T")
U = TypeVar("U")


@dataclasses.dataclass(frozen=True, slots=True)
class Maybe(Generic[T]):
    """A container that either holds a value (:meth:`some`) or does not
    (:meth:`nothing`).

    Construct instances via :meth:`some` / :meth:`nothing`, not the
    constructor directly.

    Examples
    --------
    >>> def find_even(values: list[int]) -> Maybe[int]:
    ...     for v in values:
    ...         if v % 2 == 0:
    ...             return Maybe.some(v)
    ...     return Maybe.nothing()
    >>> find_even([1, 3, 4]).unwrap_or(-1)
    4
    >>> find_even([1, 3, 5]).unwrap_or(-1)
    -1
    >>> find_even([1, 3, 5]).is_nothing
    True
    """

    _value: Any = dataclasses.field(default=None, repr=False)
    _has_value: bool = dataclasses.field(default=False, repr=False)

    @classmethod
    def some(cls, value: T) -> Maybe[T]:
        """Construct a ``Maybe`` holding ``value``."""
        return cls(_value=value, _has_value=True)

    @classmethod
    def nothing(cls) -> Maybe[T]:
        """Construct an empty ``Maybe``."""
        return cls(_value=None, _has_value=False)

    @property
    def is_some(self) -> bool:
        """Whether this ``Maybe`` holds a value."""
        return self._has_value

    @property
    def is_nothing(self) -> bool:
        """Whether this ``Maybe`` is empty."""
        return not self._has_value

    def unwrap(self) -> T:
        """Return the held value.

        Raises
        ------
        ValueError
            If this ``Maybe`` is empty.
        """
        if not self._has_value:
            raise ValueError("Cannot unwrap an empty Maybe (Maybe.nothing()).")
        return cast(T, self._value)

    def unwrap_or(self, default: T) -> T:
        """Return the held value, or ``default`` if empty."""
        return cast(T, self._value) if self._has_value else default

    def unwrap_or_else(self, fn: Callable[[], T]) -> T:
        """Return the held value, or the result of calling ``fn()`` if empty."""
        return cast(T, self._value) if self._has_value else fn()

    def map(self, fn: Callable[[T], U]) -> Maybe[U]:
        """Transform the held value, leaving an empty ``Maybe`` untouched."""
        if self._has_value:
            return Maybe.some(fn(cast(T, self._value)))
        return cast("Maybe[U]", self)

    def and_then(self, fn: Callable[[T], Maybe[U]]) -> Maybe[U]:
        """Chain another ``Maybe``-returning operation, short-circuiting on empty."""
        if self._has_value:
            return fn(cast(T, self._value))
        return cast("Maybe[U]", self)

    def filter(self, predicate: Callable[[T], bool]) -> Maybe[T]:
        """Keep the value only if it satisfies ``predicate``, else become empty."""
        if self._has_value and predicate(cast(T, self._value)):
            return self
        return Maybe.nothing()

    def to_result(self, error: Exception | str) -> Result[T]:
        """Convert to a :class:`~mineproductivity.core.result.Result`, using
        ``error`` if this ``Maybe`` is empty."""
        if self._has_value:
            return Result.ok(cast(T, self._value))
        return Result.err(error)

    def __bool__(self) -> bool:
        return self._has_value

    def __repr__(self) -> str:
        if self._has_value:
            return f"Maybe.some({self._value!r})"
        return "Maybe.nothing()"
