"""``BaseVersionedObject``: adds a monotonic integer version to an immutable
value object, supporting optimistic-concurrency-style workflows.
"""

from __future__ import annotations

import dataclasses
from typing import Self

from mineproductivity.core.exceptions import ValidationError
from mineproductivity.core.value_object import BaseValueObject

__all__ = ["BaseVersionedObject"]


@dataclasses.dataclass(frozen=True, slots=True)
class BaseVersionedObject(BaseValueObject):
    """A value object carrying an explicit, monotonically increasing version.

    Because value objects are immutable, "changing" a versioned object
    means producing a new instance with an incremented version via
    :meth:`next_version`, rather than mutating the original in place. This
    is the building block for optimistic-concurrency patterns: callers
    persist a version alongside the object and reject writes whose
    expected version does not match the currently stored one.

    Examples
    --------
    >>> from dataclasses import dataclass
    >>> @dataclass(frozen=True, slots=True)
    ... class Note(BaseVersionedObject):
    ...     text: str
    >>> note = Note(text="draft")
    >>> updated = note.next_version()
    >>> updated.version
    2
    """

    version: int = dataclasses.field(default=1, kw_only=True)

    def validate(self) -> None:
        if self.version < 1:
            raise ValidationError("BaseVersionedObject.version must be >= 1.")

    def next_version(self) -> Self:
        """Return a new instance identical to this one but with ``version + 1``."""
        return self.replace(version=self.version + 1)
