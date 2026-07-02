"""``CycleEvent``: one completed haul cycle."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["CycleEvent"]

_LEG_FIELDS = ("queue_min", "spot_min", "load_min", "haul_min", "dump_min", "return_min")


@dataclasses.dataclass(frozen=True, slots=True)
class CycleEvent(BaseEvent):
    """One completed haul cycle: queue → spot → load → haul → dump → return.

    Examples
    --------
    >>> cycle = CycleEvent(
    ...     equipment_id="HT-214", shift_id="A-2026-06-25",
    ...     queue_min=1.5, spot_min=0.5, load_min=2.5,
    ...     haul_min=8.0, dump_min=1.0, return_min=6.0,
    ...     payload_t=220.0,
    ... )
    >>> cycle.cycle_min
    19.5
    """

    event_type_code: ClassVar[str] = "CYCLE"

    queue_min: float
    spot_min: float
    load_min: float
    haul_min: float
    dump_min: float
    return_min: float
    payload_t: float
    route_id: str | None = dataclasses.field(default=None, kw_only=True)
    operator_id: str | None = dataclasses.field(default=None, kw_only=True)
    material_type: str = dataclasses.field(default="unspecified", kw_only=True)

    @property
    def cycle_min(self) -> float:
        """The total cycle duration: the sum of all six legs."""
        return (
            self.queue_min
            + self.spot_min
            + self.load_min
            + self.haul_min
            + self.dump_min
            + self.return_min
        )

    def duration_h(self) -> float:
        return self.cycle_min / 60.0

    def validate(self) -> None:
        if self.payload_t < 0:
            raise EventValidationError("CycleEvent.payload_t must be >= 0")
        legs = (
            self.queue_min,
            self.spot_min,
            self.load_min,
            self.haul_min,
            self.dump_min,
            self.return_min,
        )
        if any(leg < 0 for leg in legs):
            raise EventValidationError(
                f"CycleEvent leg minutes must be >= 0: {dict(zip(_LEG_FIELDS, legs, strict=True))}"
            )
