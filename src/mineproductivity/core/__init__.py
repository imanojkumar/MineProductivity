"""``mineproductivity.core`` -- universal, domain-agnostic framework primitives.

This package defines the foundational building blocks every other
``mineproductivity`` package is built on: entities, value objects,
identifiers, metadata, specifications, repositories, factories, builders,
validators, serializers, versioned objects, configuration, and the
``Result``/``Maybe`` error-handling types.

``core`` has zero dependencies on any other ``mineproductivity`` package and
zero knowledge of the mining domain -- see ``README.md`` for the full set of
architectural rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.core``, without reaching into internal
modules::

    from mineproductivity.core import BaseEntity, Result, BaseRepository
"""

from __future__ import annotations

from mineproductivity.core.builder import BaseBuilder
from mineproductivity.core.configuration import BaseConfiguration
from mineproductivity.core.entity import BaseEntity
from mineproductivity.core.exceptions import (
    BuilderError,
    ConfigurationError,
    DuplicateError,
    MineProductivityError,
    NotFoundError,
    SerializationError,
    ValidationError,
)
from mineproductivity.core.factory import BaseFactory
from mineproductivity.core.identifier import BaseIdentifier, UUIDIdentifier
from mineproductivity.core.maybe import Maybe
from mineproductivity.core.metadata import BaseMetadata
from mineproductivity.core.repository import BaseRepository, InMemoryRepository
from mineproductivity.core.result import Result
from mineproductivity.core.serialization import (
    BaseSerializer,
    DataclassSerializer,
    SupportsFromDict,
    SupportsToDict,
    to_dict,
)
from mineproductivity.core.service import BaseService
from mineproductivity.core.specification import (
    AndSpecification,
    BaseSpecification,
    NotSpecification,
    OrSpecification,
    PredicateSpecification,
)
from mineproductivity.core.typing import Comparable, Identifiable, JSONPrimitive, JSONValue
from mineproductivity.core.validator import BaseValidator, CompositeValidator, ValidationResult
from mineproductivity.core.value_object import BaseValueObject
from mineproductivity.core.versioning import BaseVersionedObject

__all__ = [
    "AndSpecification",
    "BaseBuilder",
    "BaseConfiguration",
    "BaseEntity",
    "BaseFactory",
    "BaseIdentifier",
    "BaseMetadata",
    "BaseRepository",
    "BaseSerializer",
    "BaseService",
    "BaseSpecification",
    "BaseValidator",
    "BaseValueObject",
    "BaseVersionedObject",
    "BuilderError",
    "Comparable",
    "CompositeValidator",
    "ConfigurationError",
    "DataclassSerializer",
    "DuplicateError",
    "Identifiable",
    "InMemoryRepository",
    "JSONPrimitive",
    "JSONValue",
    "Maybe",
    "MineProductivityError",
    "NotFoundError",
    "NotSpecification",
    "OrSpecification",
    "PredicateSpecification",
    "Result",
    "SerializationError",
    "SupportsFromDict",
    "SupportsToDict",
    "UUIDIdentifier",
    "ValidationError",
    "ValidationResult",
    "to_dict",
]
