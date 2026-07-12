"""``TaskState``: one task's condition as of the last executed step
(design spec §11).

Reuse audit: ``core.BaseValueObject`` and the
``MappingProxyType``-freezing convention reused verbatim;
``attributes`` is the same open escape hatch
``optimization.OptimizationState.attributes`` establishes (spec 10
§11), carrying model-specific progress, intermediate reasoning
artifacts, the delegation chain (design spec §18), and -- in the
reference evaluation strategy -- the ``"required_capabilities"``
entry ``PolicyEngine`` (§10) reads.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.agents.exceptions import AgentValidationError

__all__ = ["TaskState"]


@dataclasses.dataclass(frozen=True, slots=True)
class TaskState(BaseValueObject):
    """One task's attributes as of the last executed step -- a frozen
    value object; the entity is ``Task`` (design spec §11).
    Deliberately **not** an ``AgentResult`` subclass (§20): it
    represents the task's condition itself, not the outcome of an
    orchestration call about it.

    Examples
    --------
    >>> TaskState(attributes={"progress": 0.5}).attributes["progress"]
    0.5
    """

    attributes: Mapping[str, Any]

    def _normalize(self) -> None:
        super(TaskState, self)._normalize()
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def validate(self) -> None:
        if not self.attributes:
            raise AgentValidationError("TaskState.attributes must not be empty")
