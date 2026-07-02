"""``DelayEvent``: one delay, classified into a canonical category."""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from mineproductivity.ontology import DelayCategory

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["DelayEvent"]


@dataclasses.dataclass(frozen=True, slots=True)
class DelayEvent(BaseEvent):
    """One delay event, classified into exactly one of the six canonical,
    mutually-exclusive :class:`~mineproductivity.ontology.DelayCategory`
    values (Developer & Cookbook Guide Part III, "Canonical Semantics").

    Examples
    --------
    >>> delay = DelayEvent(
    ...     equipment_id="CR-01", shift_id="A-2026-06-25",
    ...     delay_category=DelayCategory.EQUIPMENT,
    ...     delay_reason="crusher_down", duration_min=252.0,
    ... )
    >>> delay.duration_h()
    4.2
    """

    event_type_code: ClassVar[str] = "DELAY"

    delay_category: DelayCategory
    delay_reason: str
    duration_min: float

    def duration_h(self) -> float:
        return self.duration_min / 60.0

    def validate(self) -> None:
        if self.duration_min < 0:
            raise EventValidationError("DelayEvent.duration_min must be >= 0")
        if not self.delay_reason.strip():
            raise EventValidationError("DelayEvent.delay_reason must not be empty")
