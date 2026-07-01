"""``BaseValueObject``: the immutable, structurally-equal building block for
every descriptive (non-identity-bearing) domain concept in ``mineproductivity``.
"""

from __future__ import annotations

import dataclasses
from typing import Self

__all__ = ["BaseValueObject"]


@dataclasses.dataclass(frozen=True, slots=True)
class BaseValueObject:
    """Base class for immutable objects whose equality is defined entirely by
    their attribute values, never by identity.

    Subclasses must be decorated with ``@dataclasses.dataclass(frozen=True)``
    (``slots=True`` is recommended for memory efficiency). Equality and
    hashing are then derived automatically by the dataclass machinery from
    the declared fields -- two value objects of the same type with equal
    fields are equal and hash identically, by design.

    Two extension hooks run automatically after ``__init__``, in this order:

    1. :meth:`_normalize` -- coerce or defensively copy mutable inputs
       (e.g. wrap a ``list`` argument in a ``tuple``, or freeze a ``dict``
       into a ``MappingProxyType``) before validation runs.
    2. :meth:`validate` -- raise an exception (conventionally
       :class:`~mineproductivity.core.exceptions.ValidationError`) if the
       instance violates a domain invariant.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True)
    ... class Money(BaseValueObject):
    ...     amount: int
    ...     currency: str
    ...
    ...     def validate(self) -> None:
    ...         if self.amount < 0:
    ...             raise ValueError("amount must be non-negative")
    >>> Money(10, "USD") == Money(10, "USD")
    True
    >>> Money(10, "USD").replace(amount=20)
    Money(amount=20, currency='USD')
    """

    def __post_init__(self) -> None:
        self._normalize()
        self.validate()

    def _normalize(self) -> None:
        """Override to coerce or defensively copy mutable fields.

        Runs before :meth:`validate`. The default implementation does
        nothing. Because instances are frozen, implementations must use
        ``object.__setattr__(self, "field_name", value)`` to assign
        normalized values.
        """

    def validate(self) -> None:
        """Override to enforce invariants on this value object's fields.

        The default implementation does nothing (no invariants).

        Raises
        ------
        Exception
            Any exception may be raised to reject invalid state;
            :class:`~mineproductivity.core.exceptions.ValidationError` is
            preferred for consistency with the rest of the framework.
        """

    def replace(self, **changes: object) -> Self:
        """Return a new instance with the given fields replaced.

        Thin, discoverable wrapper around :func:`dataclasses.replace` so
        callers do not need to import :mod:`dataclasses` themselves. The
        replacement instance goes through :meth:`_normalize` and
        :meth:`validate` again, exactly as if it had been constructed
        directly.
        """
        return dataclasses.replace(self, **changes)
