"""``Result[T]``: an explicit, exception-free way to represent an operation
that either succeeds with a value or fails with an error.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, Generic, TypeVar, cast

from mineproductivity.core.exceptions import MineProductivityError

__all__ = ["Result"]

T = TypeVar("T")
U = TypeVar("U")


@dataclasses.dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """The outcome of an operation that can fail, without raising.

    Construct instances via :meth:`ok` / :meth:`err`, not the constructor
    directly -- the underscore-prefixed fields exist only so that
    ``dataclasses`` can provide equality, hashing, and a base ``repr`` for
    free; :meth:`__post_init__` enforces that exactly one of a value or an
    error is ever present.

    Examples
    --------
    >>> def divide(a: float, b: float) -> Result[float]:
    ...     if b == 0:
    ...         return Result.err("division by zero")
    ...     return Result.ok(a / b)
    >>> divide(10, 2).unwrap()
    5.0
    >>> divide(10, 0).unwrap_or(0.0)
    0.0
    >>> divide(10, 2).map(lambda x: x * 2).unwrap()
    10.0
    """

    _value: Any = dataclasses.field(default=None, repr=False)
    _error: Exception | None = dataclasses.field(default=None, repr=False)
    _is_ok: bool = dataclasses.field(default=True, repr=False)

    def __post_init__(self) -> None:
        if self._is_ok and self._error is not None:
            raise ValueError("An Ok Result cannot carry an error.")
        if not self._is_ok and self._error is None:
            raise ValueError("An Err Result must carry an error.")

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Construct a successful result wrapping ``value``."""
        return cls(_value=value, _error=None, _is_ok=True)

    @classmethod
    def err(cls, error: Exception | str) -> Result[T]:
        """Construct a failed result wrapping ``error``.

        A plain string is wrapped in
        :class:`~mineproductivity.core.exceptions.MineProductivityError`
        for convenience.
        """
        if isinstance(error, str):
            error = MineProductivityError(error)
        return cls(_value=None, _error=error, _is_ok=False)

    @property
    def is_ok(self) -> bool:
        """Whether this result represents success."""
        return self._is_ok

    @property
    def is_err(self) -> bool:
        """Whether this result represents failure."""
        return not self._is_ok

    @property
    def value(self) -> T:
        """The success value.

        Raises
        ------
        Exception
            The stored error, if this is an ``Err`` result.
        """
        if not self._is_ok:
            raise cast(Exception, self._error)
        return cast(T, self._value)

    @property
    def error(self) -> Exception:
        """The stored error.

        Raises
        ------
        ValueError
            If this is an ``Ok`` result (which has no error).
        """
        if self._is_ok:
            raise ValueError("Result.error accessed on an Ok result.")
        return cast(Exception, self._error)

    def unwrap(self) -> T:
        """Alias for :attr:`value`, for parity with Rust/``returns``-style APIs."""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Return the success value, or ``default`` if this is an ``Err``."""
        return cast(T, self._value) if self._is_ok else default

    def unwrap_or_else(self, fn: Callable[[Exception], T]) -> T:
        """Return the success value, or the result of calling ``fn(error)``."""
        return cast(T, self._value) if self._is_ok else fn(cast(Exception, self._error))

    def map(self, fn: Callable[[T], U]) -> Result[U]:
        """Transform the success value, leaving an ``Err`` untouched."""
        if self._is_ok:
            return Result.ok(fn(cast(T, self._value)))
        return cast("Result[U]", self)

    def map_err(self, fn: Callable[[Exception], Exception]) -> Result[T]:
        """Transform the error, leaving an ``Ok`` untouched."""
        if self._is_ok:
            return self
        return Result.err(fn(cast(Exception, self._error)))

    def and_then(self, fn: Callable[[T], Result[U]]) -> Result[U]:
        """Chain another fallible operation, short-circuiting on ``Err``."""
        if self._is_ok:
            return fn(cast(T, self._value))
        return cast("Result[U]", self)

    def __bool__(self) -> bool:
        return self._is_ok

    def __repr__(self) -> str:
        if self._is_ok:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"
