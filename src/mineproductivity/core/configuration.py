"""``BaseConfiguration``: an immutable, validated settings container."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, Self

from mineproductivity.core.exceptions import ConfigurationError
from mineproductivity.core.value_object import BaseValueObject

__all__ = ["BaseConfiguration"]


@dataclasses.dataclass(frozen=True, slots=True)
class BaseConfiguration(BaseValueObject):
    """Base class for immutable, validated configuration objects.

    ``BaseConfiguration`` only defines the *shape* of configuration
    (immutable, self-validating, constructible from a plain mapping); it
    has no opinion on *where* configuration values come from (environment
    variables, files, a remote config service). Sourcing configuration is
    the responsibility of the ``mineproductivity.config`` package, which
    depends on ``core`` and produces instances of ``BaseConfiguration``
    subclasses -- ``core`` itself performs no I/O.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True)
    ... class RetrySettings(BaseConfiguration):
    ...     max_attempts: int = 3
    >>> RetrySettings.from_mapping({"max_attempts": 5}).max_attempts
    5
    """

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Self:
        """Construct an instance from a plain mapping of field values."""
        try:
            return cls(**data)
        except TypeError as exc:
            raise ConfigurationError(
                f"Could not build {cls.__name__} from mapping {data!r}: {exc}"
            ) from exc

    def to_mapping(self) -> dict[str, Any]:
        """Return this configuration's fields as a plain ``dict``."""
        return dataclasses.asdict(self)
