"""``BaseMetadata``: a generic, domain-agnostic container for descriptive
information attached to other objects (name, description, tags, arbitrary
attributes).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core.exceptions import ValidationError
from mineproductivity.core.value_object import BaseValueObject

__all__ = ["BaseMetadata"]


@dataclasses.dataclass(frozen=True, slots=True)
class BaseMetadata(BaseValueObject):
    """Descriptive metadata that can be attached to any domain object.

    ``BaseMetadata`` deliberately knows nothing about *what* it describes:
    downstream packages (e.g. a future ``kpis`` package attaching units and
    provenance to a metric) compose it into their own metadata types
    rather than subclassing it with domain-specific fields, keeping
    ``core`` free of domain knowledge. This mirrors the platform-wide
    metadata-first principle: every object that needs describing gets a
    ``BaseMetadata``-shaped companion before it gets behavior.

    Attributes
    ----------
    name:
        A short, human-readable, non-empty label.
    description:
        A longer free-text description. Empty by default.
    tags:
        An immutable set of free-form classification tags.
    attributes:
        An immutable mapping of arbitrary additional key/value data.

    Examples
    --------
    >>> meta = BaseMetadata(name="example", tags=["a", "b"], attributes={"k": 1})
    >>> sorted(meta.tags)
    ['a', 'b']
    >>> meta.attributes["k"]
    1
    """

    name: str
    description: str = dataclasses.field(default="", kw_only=True)
    tags: frozenset[str] = dataclasses.field(default_factory=frozenset, kw_only=True)
    attributes: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("BaseMetadata.name must be a non-empty string.")
