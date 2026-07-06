"""``BaseSerializer`` and structural (Protocol-based) serialization helpers."""

from __future__ import annotations

import copy
import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, Protocol, TypeVar, cast, runtime_checkable

from mineproductivity.core.exceptions import SerializationError

__all__ = [
    "BaseSerializer",
    "DataclassSerializer",
    "SupportsFromDict",
    "SupportsToDict",
    "to_dict",
]

T = TypeVar("T")


def _asdict_recursive(obj: Any) -> Any:
    """Recursively converts ``obj`` into plain, JSON-safe values -- a
    drop-in replacement for :func:`dataclasses.asdict`'s own recursion
    (dataclass fields, lists/tuples, namedtuples, dicts) that additionally
    normalizes any :class:`~collections.abc.Mapping` which is not already a
    plain ``dict``.

    ``dataclasses.asdict`` only special-cases ``isinstance(obj, dict)``;
    everything else -- including ``types.MappingProxyType``, the type
    :meth:`~mineproductivity.core.value_object.BaseValueObject._normalize`
    is documented to freeze mutable mapping fields into -- falls through to
    its ``copy.deepcopy`` fallback, which cannot pickle a ``mappingproxy``
    and raises ``TypeError``. Widening the dict check to ``Mapping``
    (``dict``'s own ABC, which ``mappingproxy`` also satisfies) is the one
    behavioral difference from ``dataclasses.asdict``; every other branch
    mirrors it exactly.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _asdict_recursive(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, tuple) and hasattr(obj, "_fields"):
        return type(obj)(*(_asdict_recursive(v) for v in obj))
    if isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_recursive(v) for v in obj)
    if isinstance(obj, Mapping):
        return {_asdict_recursive(k): _asdict_recursive(v) for k, v in obj.items()}
    return copy.deepcopy(obj)


@runtime_checkable
class SupportsToDict(Protocol):
    """Structural type for any object exposing a ``to_dict()`` method."""

    def to_dict(self) -> Mapping[str, Any]: ...


@runtime_checkable
class SupportsFromDict(Protocol):
    """Structural type for any type exposing a ``from_dict(...)`` classmethod."""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Any: ...


class BaseSerializer(ABC, Generic[T]):
    """Converts between an in-memory object of type ``T`` and a plain,
    JSON-safe mapping.

    Serialization is deliberately kept out of the object being serialized
    (composition over inheritance): a domain type does not need to know
    *how* it will be serialized, only that a ``BaseSerializer`` exists
    that can do it, which keeps formats (JSON, a database row, a wire
    protocol) fully swappable without touching the domain type.
    """

    @abstractmethod
    def serialize(self, obj: T) -> Mapping[str, Any]:
        """Convert ``obj`` into a plain mapping of primitive values."""

    @abstractmethod
    def deserialize(self, data: Mapping[str, Any]) -> T:
        """Reconstruct an instance of ``T`` from a plain mapping."""


class DataclassSerializer(BaseSerializer[T]):
    """A ready-to-use :class:`BaseSerializer` for any ``dataclasses``-based type.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True)
    ... class Point:
    ...     x: int
    ...     y: int
    >>> serializer = DataclassSerializer(Point)
    >>> data = serializer.serialize(Point(1, 2))
    >>> serializer.deserialize(data)
    Point(x=1, y=2)
    """

    def __init__(self, target_type: type[T]) -> None:
        if not dataclasses.is_dataclass(target_type):
            raise SerializationError(
                f"{target_type!r} is not a dataclass; DataclassSerializer requires one."
            )
        self._target_type = target_type

    def serialize(self, obj: T) -> dict[str, Any]:
        if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
            raise SerializationError(f"{obj!r} is not a dataclass instance.")
        return cast(dict[str, Any], _asdict_recursive(obj))

    def deserialize(self, data: Mapping[str, Any]) -> T:
        try:
            return self._target_type(**data)
        except TypeError as exc:
            raise SerializationError(
                f"Could not deserialize {self._target_type.__name__} from {data!r}: {exc}"
            ) from exc


def to_dict(obj: Any) -> dict[str, Any]:
    """Best-effort conversion of ``obj`` into a plain ``dict``.

    Prefers a ``to_dict()`` method if ``obj`` implements
    :class:`SupportsToDict`; falls back to :func:`dataclasses.asdict`-equivalent
    recursion (see :func:`_asdict_recursive`) for plain dataclass instances.

    Raises
    ------
    SerializationError
        If neither strategy applies.
    """
    if isinstance(obj, SupportsToDict):
        return dict(obj.to_dict())
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return cast(dict[str, Any], _asdict_recursive(obj))
    raise SerializationError(f"Object of type {type(obj).__name__!r} is not serializable.")
