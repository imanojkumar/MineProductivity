"""``AgentMetadata``/``AgentCategory``: the minimal registration
schema for a discoverable
:class:`~mineproductivity.agents.abstractions.Agent` type (design spec
§29).

Reuse audit: ``core.BaseMetadata`` reused verbatim; the whole module
mirrors ``optimization.metadata``/``simulation.metadata``
field-for-field, including the name-defaults-to-code convention. The
ten category members are domain roles rather than algorithmic
paradigms (design spec §8) -- a category scopes *what evidence and
permissions* an agent reads, never *how* it decides.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.agents.exceptions import AgentValidationError

__all__ = ["AgentCategory", "AgentMetadata"]


class AgentCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``optimization.OptimizationCategory``'s closed-enum rule
    (spec 10 §29)."""

    PRODUCTION = "production"
    DISPATCH = "dispatch"
    FLEET = "fleet"
    MAINTENANCE = "maintenance"
    DRILL_AND_BLAST = "drill_and_blast"
    SHIFT_SUPERVISOR = "shift_supervisor"
    ESG = "esg"
    SAFETY = "safety"
    EXECUTIVE_ADVISOR = "executive_advisor"
    PLANNING = "planning"


@dataclasses.dataclass(frozen=True, slots=True)
class AgentMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable ``Agent``
    type (design spec §29). ``code`` names a **type** (e.g.
    ``"FLEET.ReassignmentAdvisor"``), never a ``Task.id``.

    Examples
    --------
    >>> meta = AgentMetadata(
    ...     code="FLEET.ReassignmentAdvisor",
    ...     category=AgentCategory.FLEET,
    ...     description="Advises on truck reassignment after a breakdown.",
    ... )
    >>> meta.name
    'FLEET.ReassignmentAdvisor'
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: AgentCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(AgentMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise AgentValidationError("AgentMetadata.code must not be empty")
        if not isinstance(self.category, AgentCategory):
            raise AgentValidationError(
                f"AgentMetadata.category must be an AgentCategory member, got {self.category!r}"
            )
        super(AgentMetadata, self).validate()
