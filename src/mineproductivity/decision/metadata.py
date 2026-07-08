"""``DecisionMetadata``: the minimal registration schema for a
discoverable :class:`~mineproductivity.decision.abstractions.DecisionModel`.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.decision.exceptions import DecisionValidationError

__all__ = ["DecisionCategory", "DecisionMetadata"]


class DecisionCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``analytics.AnalyticsCategory``'s closed-enum rule
    (design spec §31)."""

    STRATEGY = "strategy"
    RANKING = "ranking"
    ROOT_CAUSE = "root_cause"
    WHAT_IF = "what_if"


@dataclasses.dataclass(frozen=True, slots=True)
class DecisionMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable
    ``DecisionModel`` -- as light as ``analytics.AnalyticsMetadata``, not
    as heavy as ``kpis.KPIMetadata``, because a ``DecisionModel``
    implementation is a computational strategy, not itself the governed
    business artifact (that weight belongs to ``Policy``, design spec
    §12, §3.6).

    ``BaseMetadata.name`` has no default upstream and a ``DecisionModel``'s
    ``code`` already serves as its identifier, so ``name`` defaults to
    ``code`` (via :meth:`_normalize`) whenever a caller does not supply
    one explicitly -- the same convention ``AnalyticsMetadata`` already
    established.

    Examples
    --------
    >>> meta = DecisionMetadata(
    ...     code="STRATEGY.Threshold", category=DecisionCategory.STRATEGY,
    ...     description="Evaluate a Policy's rules against a DecisionContext.",
    ... )
    >>> meta.code
    'STRATEGY.Threshold'
    >>> meta.name
    'STRATEGY.Threshold'
    >>> DecisionMetadata(code="", category=DecisionCategory.STRATEGY, description="x")
    Traceback (most recent call last):
        ...
    mineproductivity.decision.exceptions.DecisionValidationError: DecisionMetadata.code must not be empty
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: DecisionCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(DecisionMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise DecisionValidationError("DecisionMetadata.code must not be empty")
        super(DecisionMetadata, self).validate()
