"""``TwinResult``: the shared envelope every concrete digital-twin
outcome composes, and the two concrete results built on it (design spec
§25).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseValueObject`` is reused verbatim as every type's base, and
the ``MappingProxyType``-freezing convention for ``Mapping``-typed
fields is reused exactly as ``decision.result``/``analytics.result``
already established -- no new value-object base or envelope concept is
introduced; ``TwinResult`` mirrors ``decision.DecisionResult``'s role
(spec 07 §28) one layer up, field-for-field in shape (``twin_id``
substituting for ``model_code`` as the traceability key).
``TwinState``/``TwinSnapshot`` are deliberately **not** ``TwinResult``
subclasses: each represents the twin's condition itself, not the
outcome of one orchestration call *about* the twin -- the same
distinction spec 07 §28 already drew between ``DecisionResult`` and the
plain ``BaseValueObject``\\ s attached to but not themselves results of
a decision.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.state import TwinState

__all__ = ["SyncResult", "TwinResult", "TwinSimulationResult"]


@dataclasses.dataclass(frozen=True, slots=True)
class TwinResult(BaseValueObject):
    """The shared envelope every concrete digital-twin outcome composes
    -- mirrors ``decision.DecisionResult``'s role (spec 07 §28), one
    layer up.

    Examples
    --------
    >>> TwinResult(twin_id="CONV-7").twin_id
    'CONV-7'
    >>> TwinResult(warnings=("no events to apply",)).warnings
    ('no events to apply',)
    """

    twin_id: str = dataclasses.field(default="", kw_only=True)
    computed_at: datetime = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc), kw_only=True
    )
    warnings: tuple[str, ...] = dataclasses.field(default=(), kw_only=True)


@dataclasses.dataclass(frozen=True, slots=True)
class SyncResult(TwinResult):
    """The outcome of one ``TwinSynchronizer.synchronize()`` call
    (design spec §11, §25). ``warnings`` (inherited) is the primary
    "why didn't this twin's state change the way I expected" signal
    (§24) -- a legitimately-empty or legitimately-unchanged sync returns
    a warning-carrying ``SyncResult``, never raises.

    Examples
    --------
    >>> result = SyncResult(
    ...     twin_id="CONV-7",
    ...     previous_status=TwinStatus.PROVISIONED,
    ...     new_status=TwinStatus.SYNCHRONIZED,
    ...     events_applied=3,
    ... )
    >>> result.events_applied
    3
    """

    previous_status: TwinStatus
    new_status: TwinStatus
    events_applied: int


@dataclasses.dataclass(frozen=True, slots=True)
class TwinSimulationResult(TwinResult):
    """The outcome of one ``TwinSimulationModel._simulate()`` call -- a
    stub-shaped result type defined now even though no producer of it
    ships in this release (design spec §14, §25), exactly as
    ``decision.WhatIfResult``/``analytics.ForecastResult`` were defined
    ahead of any concrete implementation (spec 07 §19, spec 06 §16).

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> result = TwinSimulationResult(
    ...     twin_id="CONV-7",
    ...     hypothesis={"belt_speed_mps": 3.5},
    ...     predicted_state=TwinState(
    ...         attributes={"belt_speed_mps": 3.5},
    ...         captured_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ...     ),
    ... )
    >>> result.hypothesis["belt_speed_mps"]
    3.5
    """

    hypothesis: Mapping[str, Any]
    predicted_state: TwinState

    def _normalize(self) -> None:
        super(TwinSimulationResult, self)._normalize()
        object.__setattr__(self, "hypothesis", MappingProxyType(dict(self.hypothesis)))
