"""``SimulationMetadata``/``SimulationCategory``: the minimal
registration schema for a discoverable
:class:`~mineproductivity.simulation.abstractions.SimulationModel` type
(design spec §29).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseMetadata`` is reused verbatim as the base, and the whole
module mirrors ``digital_twin.metadata``/``decision.metadata``
field-for-field (design spec §29: "as light as
``digital_twin.TwinMetadata``/``decision.DecisionMetadata``... not as
heavy as ``kpis.KPIMetadata``, because a ``SimulationModel`` type is a
computational strategy, not itself a governed business artifact -- that
weight belongs to ``Scenario``, §9"). No new metadata mechanism,
closed-enum convention, or name-defaulting rule is introduced.
"""

from __future__ import annotations

import dataclasses
from enum import Enum

from mineproductivity.core import BaseMetadata

from mineproductivity.simulation.exceptions import SimulationValidationError

__all__ = ["SimulationCategory", "SimulationMetadata"]


class SimulationCategory(Enum):
    """Closed enum -- adding a member is a governance-reviewed change,
    mirroring ``digital_twin.TwinCategory``'s/``decision.DecisionCategory``'s
    closed-enum rule (spec 08 §26, spec 07 §30)."""

    MONTE_CARLO = "monte_carlo"
    DISCRETE_EVENT = "discrete_event"
    SYSTEM_DYNAMICS = "system_dynamics"
    CALIBRATION = "calibration"


@dataclasses.dataclass(frozen=True, slots=True)
class SimulationMetadata(BaseMetadata):
    """The minimal registration schema for a discoverable
    ``SimulationModel`` type (design spec §29). ``code`` names a
    **type** (e.g. ``"MONTECARLO.HaulCycleVariability"``), never a
    **run** -- the same distinction spec 08 §26 draws between
    ``TwinMetadata.code`` and ``Twin.id``, applied here between a model
    type's code and a ``SimulationRun.id``.

    ``BaseMetadata.name`` has no default upstream and a model type's
    ``code`` already serves as its identifier, so ``name`` defaults to
    ``code`` (via :meth:`_normalize`) whenever a caller does not supply
    one explicitly -- the same convention ``TwinMetadata``/
    ``DecisionMetadata`` already established.

    Examples
    --------
    >>> meta = SimulationMetadata(
    ...     code="MONTECARLO.HaulCycleVariability",
    ...     category=SimulationCategory.MONTE_CARLO,
    ...     description="Randomized haul-cycle variability trials.",
    ... )
    >>> meta.name
    'MONTECARLO.HaulCycleVariability'
    >>> meta.version
    '1.0.0'
    >>> SimulationMetadata(code="", category=SimulationCategory.MONTE_CARLO, description="x")
    Traceback (most recent call last):
        ...
    mineproductivity.simulation.exceptions.SimulationValidationError: SimulationMetadata.code must not be empty
    """

    name: str = dataclasses.field(default="", kw_only=True)
    code: str
    category: SimulationCategory = dataclasses.field(kw_only=True)
    description: str = dataclasses.field(kw_only=True)
    version: str = dataclasses.field(default="1.0.0", kw_only=True)

    def _normalize(self) -> None:
        super(SimulationMetadata, self)._normalize()
        if not self.name:
            object.__setattr__(self, "name", self.code)

    def validate(self) -> None:
        if not self.code.strip():
            raise SimulationValidationError("SimulationMetadata.code must not be empty")
        if not isinstance(self.category, SimulationCategory):
            raise SimulationValidationError(
                f"SimulationMetadata.category must be a SimulationCategory member, "
                f"got {self.category!r}"
            )
        super(SimulationMetadata, self).validate()
