"""Shared typing primitives (TypeVars, Protocols, type aliases) used across
``mineproductivity.core`` and, by extension, every package built on it.

Nothing in this module has any runtime behavior beyond structural type
checks (``isinstance`` against ``@runtime_checkable`` Protocols); it exists
purely to give the rest of the package a single, consistent vocabulary for
generic and structural typing.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any, Protocol, TypeVar, runtime_checkable

__all__ = [
    "Comparable",
    "Identifiable",
    "JSONPrimitive",
    "JSONValue",
    "T",
    "TId",
    "U",
]

T = TypeVar("T")
"""A generic, unconstrained type variable used for a single "payload" type."""

U = TypeVar("U")
"""A second generic, unconstrained type variable, used alongside :data:`T`
when a mapping/transform between two types is being described (e.g.
``Callable[[T], U]``)."""

TId = TypeVar("TId", bound=Hashable)
"""A type variable for identifier/identity values. Bound to :class:`~collections.abc.Hashable`
because identifiers are used as mapping keys (see
:class:`~mineproductivity.core.repository.BaseRepository`) and as the basis
for entity equality (see :class:`~mineproductivity.core.entity.BaseEntity`)."""

type JSONPrimitive = str | int | float | bool | None
"""A single JSON scalar value."""

type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
"""Any value representable in JSON: a primitive, or a list/dict of
:data:`JSONValue`. Defined with PEP 695 ``type`` syntax so the recursive
reference resolves lazily without manual forward-reference quoting."""


@runtime_checkable
class Comparable(Protocol):
    """Structural type for anything supporting ``<`` comparison.

    Satisfied by any object implementing ``__lt__``, without requiring
    inheritance from a common base -- useful for generic sorting/ranking
    utilities that should accept both ``core`` types and plain built-ins
    (``int``, ``str``, ``datetime``, ...).
    """

    def __lt__(self, other: Any) -> bool: ...


@runtime_checkable
class Identifiable(Protocol[TId]):
    """Structural type for anything exposing an ``id`` attribute.

    Satisfied by any :class:`~mineproductivity.core.entity.BaseEntity`
    instance, but also by any unrelated class that happens to expose an
    ``id`` attribute -- callers that only need "has an id" rather than
    "is-a Entity" should prefer this Protocol over importing
    :class:`~mineproductivity.core.entity.BaseEntity` directly.
    """

    id: TId
