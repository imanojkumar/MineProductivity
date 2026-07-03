"""``BaseEntityType``: the root of every ontology entity type."""

from __future__ import annotations

import dataclasses
import types
import typing
from abc import ABC
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from mineproductivity.core import BaseEntity, BaseMetadata, DuplicateError, Maybe

from mineproductivity.ontology.exceptions import UnknownEntityTypeError

__all__ = ["BaseEntityType", "EntityTypeMetadata", "register_entity_type"]

_JSON_TYPE_BY_PYTHON_TYPE: Mapping[type, str] = {
    str: "string",
    float: "number",
    int: "integer",
    bool: "boolean",
    datetime: "string",
}


@dataclasses.dataclass(frozen=True, slots=True)
class EntityTypeMetadata(BaseMetadata):
    """Every entity type's descriptive metadata, in addition to
    :class:`~mineproductivity.core.metadata.BaseMetadata`'s
    name/description/tags/attributes.

    Mandatory per the metadata-first principle: a blank field here is a
    specification gap (mirrors the KPI Standard Library's completeness
    discipline).
    """

    supported_kpis: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)
    parent_code: str | None = dataclasses.field(default=None, kw_only=True)


def _json_type_for(field_type: Any) -> str:
    if field_type is None:
        return "string"
    origin = typing.get_origin(field_type)
    if origin in (types.UnionType, typing.Union):
        non_none = [arg for arg in typing.get_args(field_type) if arg is not type(None)]
        field_type = non_none[0] if non_none else field_type
        origin = typing.get_origin(field_type)
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        return "string"
    if origin in (tuple, list, frozenset, set):
        return "array"
    if origin is dict or origin is Mapping:
        return "object"
    if isinstance(field_type, type):
        return _JSON_TYPE_BY_PYTHON_TYPE.get(field_type, "string")
    return "string"


_SCHEMA_CACHE: dict[type[Any], Mapping[str, Any]] = {}


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class BaseEntityType(BaseEntity[str], ABC):
    """Root of every ontology entity type.

    A concrete leaf (``RigidHaulTruck``, ``Pit``, ``Shift``, ...) is a
    frozen dataclass subclass declaring a unique ``code: ClassVar[str]``
    (the stable registry key), a ``meta: ClassVar[EntityTypeMetadata]``,
    and whatever domain fields the type needs. Neither ``code`` nor
    ``meta`` is given a default at this level: a leaf type that forgets
    to declare one fails loudly (``AttributeError``) the first time
    either is read (e.g. by :meth:`to_schema` or the entity type
    registry), rather than silently inheriting a placeholder value.

    Inherits :class:`~mineproductivity.core.entity.BaseEntity`'s
    identity-based equality (two instances with the same ``id`` are equal
    regardless of other fields), consistent with the Cookbook's rule that
    entities are identity-bearing, not value-bearing.

    Unlike :class:`~mineproductivity.core.value_object.BaseValueObject`,
    ``core.BaseEntity`` defines no ``__post_init__``/``validate()`` hook
    of its own (entities were not previously built on top of it by any
    implemented package). Since the design specification requires
    structural validation to be "enforced at construction" (§19),
    ``BaseEntityType`` adds that hook locally -- mirroring
    ``BaseValueObject``'s ``_normalize()``/``validate()`` pattern exactly
    -- without modifying the locked ``core`` package.
    """

    code: ClassVar[str]
    meta: ClassVar[EntityTypeMetadata]

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
        """Override to enforce invariants on this entity type's fields.

        The default implementation does nothing (no invariants).

        Raises
        ------
        Exception
            Any exception may be raised to reject invalid state;
            :class:`~mineproductivity.ontology.exceptions.OntologyValidationError`
            is preferred for consistency with the rest of this package.
        """

    def to_schema(self) -> Mapping[str, Any]:
        """Export this type's shape as JSON Schema -- read by dashboards,
        validation, and AI agents without touching source code. Cached
        per concrete type after the first call, since the schema is
        static for a given type version."""
        cls = type(self)
        cached = _SCHEMA_CACHE.get(cls)
        if cached is not None:
            return cached

        hints = typing.get_type_hints(cls)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for f in dataclasses.fields(cls):
            if f.name == "id":
                continue
            properties[f.name] = {"type": _json_type_for(hints.get(f.name))}
            has_default = (
                f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING
            )
            if not has_default:
                required.append(f.name)

        schema: Mapping[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": cls.code,
            "type": "object",
            "properties": properties,
            "required": required,
        }
        _SCHEMA_CACHE[cls] = schema
        return schema


class _EntityTypeRegistry:
    """Internal registry of ``entity_type code -> BaseEntityType subclass``.

    Populated at import time by :func:`register_entity_type`. Not part of
    the public API (design spec §9) -- consumed publicly only via the
    future Registry Framework's discovery surface. A minimal, self
    -contained mechanism exists here (rather than depending on the not
    -yet-implemented ``registry`` package) per Documentation Governance
    Rule #005's "minimum shared contract" principle, applied in reverse:
    since ``ontology`` is implemented *before* ``registry`` in this
    project's phasing, it carries its own small registration mechanism
    now and will be able to delegate to the generic ``registry.Registry``
    without a public API change once that package exists.
    """

    def __init__(self) -> None:
        self._types: dict[str, type[BaseEntityType]] = {}

    def register(self, cls: type[BaseEntityType]) -> None:
        existing = self._types.get(cls.code)
        if existing is not None and existing is not cls:
            raise DuplicateError(
                f"entity type code {cls.code!r} is already registered to "
                f"{existing.__module__}.{existing.__qualname__}"
            )
        self._types[cls.code] = cls

    def lookup(self, code: str) -> Maybe[type[BaseEntityType]]:
        found = self._types.get(code)
        return Maybe.nothing() if found is None else Maybe.some(found)

    def get(self, code: str) -> type[BaseEntityType]:
        found = self._types.get(code)
        if found is None:
            raise UnknownEntityTypeError(f"no entity type registered for code {code!r}")
        return found

    def __len__(self) -> int:
        return len(self._types)

    def __contains__(self, code: str) -> bool:
        return code in self._types

    def all_codes(self) -> tuple[str, ...]:
        return tuple(self._types.keys())


_REGISTRY = _EntityTypeRegistry()


def register_entity_type(cls: type[BaseEntityType]) -> type[BaseEntityType]:
    """Register ``cls`` into the internal entity type registry, keyed by
    ``cls.code``. Applied as a decorator to every concrete leaf type
    across all ten sub-ontology families (``register_equipment`` in
    ``ontology.equipment`` is a documented alias of this same function,
    for readability at equipment-specific call sites).

    Raises
    ------
    DuplicateError
        If ``cls.code`` is already registered to a *different* class.
    """
    _REGISTRY.register(cls)
    return cls


def lookup_entity_type(code: str) -> Maybe[type[BaseEntityType]]:
    """Non-raising lookup of a registered entity type by its ``code``."""
    return _REGISTRY.lookup(code)


def get_entity_type(code: str) -> type[BaseEntityType]:
    """Raising lookup of a registered entity type by its ``code``.

    Raises
    ------
    UnknownEntityTypeError
        If no type is registered under ``code``.
    """
    return _REGISTRY.get(code)


def registered_entity_type_codes() -> tuple[str, ...]:
    """Return every currently-registered entity type ``code``."""
    return _REGISTRY.all_codes()
