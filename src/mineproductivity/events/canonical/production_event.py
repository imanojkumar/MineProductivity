"""``ProductionEvent``: a shift-level production summary."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["ProductionEvent"]


@dataclasses.dataclass(frozen=True, slots=True)
class ProductionEvent(BaseEvent):
    """A shift-level production summary for one pit/material combination.

    Examples
    --------
    >>> event = ProductionEvent(
    ...     equipment_id="PIT-NORTH", shift_id="PIL_2026-01-15_D",
    ...     pit_code="PIT-NORTH", material_type="Ore",
    ...     tonnes_moved=38400.0, planned_tonnes=40000.0, operating_h=29.7,
    ... )
    >>> event.duration_h()
    29.7
    """

    event_type_code: ClassVar[str] = "PRODUCTION"

    pit_code: str
    material_type: str
    tonnes_moved: float
    planned_tonnes: float
    operating_h: float

    def duration_h(self) -> float:
        return self.operating_h

    def validate(self) -> None:
        if self.tonnes_moved < 0:
            raise EventValidationError("ProductionEvent.tonnes_moved must be >= 0")
        if self.planned_tonnes < 0:
            raise EventValidationError("ProductionEvent.planned_tonnes must be >= 0")
        if self.operating_h < 0:
            raise EventValidationError("ProductionEvent.operating_h must be >= 0")
