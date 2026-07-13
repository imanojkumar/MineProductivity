"""``BaseEntity``: the identity-bearing building block of the domain model."""

from __future__ import annotations

import dataclasses
from typing import Generic

from mineproductivity.core.typing import TId

__all__ = ["BaseEntity"]


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class BaseEntity(Generic[TId]):
    """Base class for objects whose identity, not their attributes, defines
    equality.

    Two entities of the same concrete type with the same :attr:`id` are
    considered equal even if every other field differs; two entities with
    different ids are never equal, even if every other field is identical.
    This mirrors the standard Domain-Driven Design definition of an
    *Entity*, as distinct from
    :class:`~mineproductivity.core.value_object.BaseValueObject`, whose
    equality is defined entirely by attribute values.

    ``BaseEntity`` is immutable (a frozen dataclass): representing a state
    change means producing a new instance -- typically via a
    ``dataclasses.replace``-style helper in a subclass -- rather than
    mutating fields in place. This is consistent with the platform's
    event-first architecture, in which entity state is a projection of an
    immutable event stream, not a mutable record.

    **Type parameter** ``TId`` — the type of this entity's identity. Any
    hashable type is acceptable, including a raw ``str``/``int``/``uuid.UUID``
    or a dedicated
    :class:`~mineproductivity.core.identifier.BaseIdentifier` subclass
    (recommended for anything beyond trivial examples, since it prevents
    accidentally comparing/mixing ids from different entity types).

    Note that ``__repr__`` is intentionally *not* overridden here: each
    concrete subclass gets the standard dataclass-generated ``repr``
    showing every field (useful for debugging), while equality and
    hashing use identity only. Every subclass must repeat
    ``eq=False`` in its own ``@dataclass`` decorator, since ``eq``
    defaults to ``True`` and would otherwise silently replace the
    identity-based ``__eq__``/``__hash__`` defined below (Python only
    skips generating a dunder method when the *subclass itself*
    defines it, not when an ancestor does).

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True, eq=False)
    ... class Truck(BaseEntity[str]):
    ...     model: str
    >>> Truck(id="T-1", model="CAT 793") == Truck(id="T-1", model="different")
    True
    >>> Truck(id="T-1", model="CAT 793") == Truck(id="T-2", model="CAT 793")
    False
    """

    id: TId

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        return type(self) is type(other) and self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
