"""``AgentResult``: the shared envelope every agent action's outcome
composes (design spec §20).

Reuse audit: ``decision.Explanation`` reused directly as the
structured, evidence-linked justification -- no second justification
type is defined (design spec §20), exactly the reuse Decision's own
Future Roadmap anticipated (spec 07 §36). ``TaskState`` (§11) is
deliberately **not** an ``AgentResult`` subclass: it represents the
task's condition itself, not the outcome of an orchestration call
about it. ``output`` is an open ``Mapping[str, Any]`` rather than a
typed field, since what an agent's action *is* varies by category
(§29) far more than what an optimization's solution is.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject
from mineproductivity.decision import Explanation

from mineproductivity.agents.tool import ToolInvocation

__all__ = ["AgentResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class AgentResult(BaseValueObject):
    """The shared envelope every concrete agent outcome composes --
    mirrors ``optimization.OptimizationResult``'s role (spec 10 §18),
    one layer up. A legitimately incomplete or ambiguous task
    surfaces as a warning here, never a raise (design spec §30's
    'qualify, don't coerce' rule).

    Examples
    --------
    >>> result = AgentResult(warnings=("no evidence in context",))
    >>> result.task_id
    ''
    >>> result.tool_invocations
    ()
    """

    task_id: str = dataclasses.field(default="")
    computed_at: datetime = dataclasses.field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: tuple[str, ...] = dataclasses.field(default=())
    output: Mapping[str, Any] = dataclasses.field(default_factory=dict, kw_only=True)
    explanation: Explanation | None = dataclasses.field(default=None, kw_only=True)
    tool_invocations: tuple[ToolInvocation, ...] = dataclasses.field(default=(), kw_only=True)

    def _normalize(self) -> None:
        super(AgentResult, self)._normalize()
        object.__setattr__(self, "output", MappingProxyType(dict(self.output)))
