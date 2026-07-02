"""``ConsumptionEvent``: one resource-consumption reading (fuel, power, water, reagent)."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import ClassVar

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["ConsumptionEvent", "ResourceType"]


class ResourceType(Enum):
    """The resource kinds a :class:`ConsumptionEvent` can meter."""

    FUEL = "fuel"
    POWER = "power"
    WATER = "water"
    REAGENT = "reagent"


@dataclasses.dataclass(frozen=True, slots=True)
class ConsumptionEvent(BaseEvent):
    """One resource-consumption reading -- e.g. a single fuel-dispensing
    event. Instantaneous by nature (a metering reading, not a span), so
    :meth:`duration_h` is always ``0.0``.

    Examples
    --------
    >>> event = ConsumptionEvent(
    ...     equipment_id="T-101", shift_id="PIL_2026-01-15_D",
    ...     resource_type=ResourceType.FUEL, quantity=1840.0, unit="L",
    ... )
    >>> event.duration_h()
    0.0
    """

    event_type_code: ClassVar[str] = "CONSUMPTION"

    resource_type: ResourceType
    quantity: float
    unit: str

    def duration_h(self) -> float:
        return 0.0

    def validate(self) -> None:
        if self.quantity < 0:
            raise EventValidationError("ConsumptionEvent.quantity must be >= 0")
        if not self.unit.strip():
            raise EventValidationError("ConsumptionEvent.unit must not be empty")
