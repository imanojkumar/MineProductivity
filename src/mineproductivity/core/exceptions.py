"""The ``mineproductivity.core`` exception hierarchy.

Every exception raised by ``mineproductivity`` framework code ultimately
derives from :class:`MineProductivityError`, so callers can catch every
framework-raised error with a single ``except`` clause while still being
able to catch a specific category (validation, configuration, lookup, ...)
when that is more useful.

This module has no dependencies on any other module in this package, so it
can safely be imported from anywhere without risk of circular imports.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = [
    "BuilderError",
    "ConfigurationError",
    "DuplicateError",
    "MineProductivityError",
    "NotFoundError",
    "SerializationError",
    "ValidationError",
]


class MineProductivityError(Exception):
    """Root of the ``mineproductivity`` exception hierarchy.

    Parameters
    ----------
    message:
        A human-readable description of the error.
    details:
        Optional structured context (e.g. the offending field name, id, or
        value) that callers can inspect programmatically instead of
        parsing the message string.
    """

    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: Mapping[str, Any] = details if details is not None else {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.message!r}, details={dict(self.details)!r})"


class ValidationError(MineProductivityError):
    """Raised when an object or candidate value fails to satisfy an invariant."""


class ConfigurationError(MineProductivityError):
    """Raised when configuration data is missing, malformed, or invalid."""


class NotFoundError(MineProductivityError):
    """Raised when a lookup (e.g. :meth:`~mineproductivity.core.repository.BaseRepository.get`)
    finds no matching object."""


class DuplicateError(MineProductivityError):
    """Raised when an operation would violate a uniqueness constraint."""


class SerializationError(MineProductivityError):
    """Raised when an object cannot be serialized or deserialized."""


class BuilderError(MineProductivityError):
    """Raised when a :class:`~mineproductivity.core.builder.BaseBuilder` is asked
    to build from incomplete or inconsistent state."""
