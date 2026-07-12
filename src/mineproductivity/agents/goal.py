"""``Goal``: the input a workflow decomposes (design spec §13).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim. A new
``success_criteria`` shape is an additive change to its open
``Mapping``, never a new typed field.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

__all__ = ["Goal"]


@dataclasses.dataclass(frozen=True, slots=True)
class Goal(BaseValueObject):
    """A named objective and its success criteria, prior to
    decomposition into one or more ``Task``\\ s (design spec §13).

    Examples
    --------
    >>> goal = Goal(
    ...     description="Recover night-shift haulage throughput",
    ...     success_criteria={"target_tph": 1200.0},
    ... )
    >>> goal.success_criteria["target_tph"]
    1200.0
    """

    description: str
    success_criteria: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)

    def _normalize(self) -> None:
        super(Goal, self)._normalize()
        object.__setattr__(self, "success_criteria", MappingProxyType(dict(self.success_criteria)))
