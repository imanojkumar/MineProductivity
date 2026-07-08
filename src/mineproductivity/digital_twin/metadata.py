"""``TwinMetadata``/``TwinCategory``: the minimal registration schema
for a discoverable :class:`~mineproductivity.digital_twin.abstractions.Twin`
type (design spec §26).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseMetadata`` is reused verbatim as the base, and the whole
module mirrors ``decision.metadata``/``analytics.metadata``
field-for-field (design spec §26: "as light as
``decision.DecisionMetadata``/``analytics.AnalyticsMetadata``... not as
heavy as ``kpis.KPIMetadata``, because a Twin *type* is a
representational strategy, not itself a governed business artifact").
No new metadata mechanism, closed-enum convention, or name-defaulting
rule is introduced -- all three are inherited from the established
sibling pattern unchanged.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.digital_twin.exceptions import TwinValidationError

__all__ = ["TwinCategory", "TwinMetadata"]


class TwinCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``decision.DecisionCategory``'s/``analytics.AnalyticsCategory``'s
    closed-enum rule (spec 07 §30, spec 06 §31)."""

    MINE = "mine"
    EQUIPMENT = "equipment"
    PLANT = "plant"
    CONVEYOR = "conveyor"
    HAULAGE = "haulage"
    FLEET = "fleet"
    PROCESSING_PLANT = "processing_plant"
    GEOLOGICAL = "geological"
    VENTILATION = "ventilation"
    STOCKPILE = "stockpile"
    PRODUCTION = "production"


@dataclasses.dataclass(frozen=True, slots=True)
class TwinMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable ``Twin`` type
    (design spec §26). ``code`` names a **type** (e.g.
    ``"CONVEYOR.Standard"``), never an **instance** -- ``Twin.id`` (§8,
    inherited from ``core.BaseEntity``) identifies "which specific
    conveyor," while ``code`` identifies "what kind of conveyor twin is
    this." Two twin instances scoped to different assets share the same
    ``code`` but never the same ``id``.

    ``BaseMetadata.name`` has no default upstream and a ``Twin`` type's
    ``code`` already serves as its identifier, so ``name`` defaults to
    ``code`` (via :meth:`_normalize`) whenever a caller does not supply
    one explicitly -- the same convention ``DecisionMetadata``/
    ``AnalyticsMetadata`` already established.

    Examples
    --------
    >>> meta = TwinMetadata(
    ...     code="CONVEYOR.Standard", category=TwinCategory.CONVEYOR,
    ...     description="A standard conveyor system twin.",
    ... )
    >>> meta.code
    'CONVEYOR.Standard'
    >>> meta.name
    'CONVEYOR.Standard'
    >>> meta.version
    '1.0.0'
    >>> TwinMetadata(code="", category=TwinCategory.CONVEYOR, description="x")
    Traceback (most recent call last):
        ...
    mineproductivity.digital_twin.exceptions.TwinValidationError: TwinMetadata.code must not be empty
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: TwinCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(TwinMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise TwinValidationError("TwinMetadata.code must not be empty")
        if not isinstance(self.category, TwinCategory):
            raise TwinValidationError(
                f"TwinMetadata.category must be a TwinCategory member, got {self.category!r}"
            )
        super(TwinMetadata, self).validate()
