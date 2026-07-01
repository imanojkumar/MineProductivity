"""``BaseIdentifier``: immutable, typed wrappers around an entity's identity value."""

from __future__ import annotations

import dataclasses
import uuid
from typing import Generic, Self, TypeVar

from mineproductivity.core.value_object import BaseValueObject

__all__ = ["BaseIdentifier", "UUIDIdentifier"]

TIdValue = TypeVar("TIdValue")


@dataclasses.dataclass(frozen=True, slots=True)
class BaseIdentifier(BaseValueObject, Generic[TIdValue]):
    """A value object that wraps a single raw identity value.

    Identifiers are themselves value objects: two identifiers wrapping
    equal raw values are equal, regardless of which entity they identify.
    Subclass this to create domain-specific identifier types (e.g.
    ``TruckId``, ``ShiftId``) instead of passing raw strings/UUIDs/ints
    around, so a type checker can catch identifier mix-ups such as passing
    a ``TruckId`` where a ``ShiftId`` is expected.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True)
    ... class TruckId(BaseIdentifier[str]):
    ...     pass
    >>> TruckId("T-1") == TruckId("T-1")
    True
    >>> str(TruckId("T-1"))
    'T-1'
    """

    value: TIdValue

    def __str__(self) -> str:
        return str(self.value)


@dataclasses.dataclass(frozen=True, slots=True)
class UUIDIdentifier(BaseIdentifier[uuid.UUID]):
    """A :class:`BaseIdentifier` backed by a standard library :class:`uuid.UUID`.

    The most common concrete identifier type: generate one with
    :meth:`generate`, or parse an existing canonical string with
    :meth:`from_string`.

    Examples
    --------
    >>> identifier = UUIDIdentifier.generate()
    >>> identifier == UUIDIdentifier.from_string(str(identifier))
    True
    """

    @classmethod
    def generate(cls) -> Self:
        """Return a new, randomly generated identifier (UUID version 4)."""
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse a canonical UUID string (e.g. ``"12345678-1234-..."``) into an identifier."""
        return cls(value=uuid.UUID(value))
