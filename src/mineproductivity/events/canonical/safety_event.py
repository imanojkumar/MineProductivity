"""``SafetyEvent``: one leading-safety-indicator observation."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import ClassVar

from mineproductivity.events.base_event import BaseEvent

__all__ = ["SafetyEvent", "SafetyEventType", "SafetySeverity"]


class SafetyEventType(Enum):
    """The leading safety-indicator kinds a :class:`SafetyEvent` can record."""

    SPEED_VIOLATION = "speed-violation"
    FATIGUE = "fatigue"
    PROXIMITY = "proximity"
    SEATBELT = "seatbelt"


class SafetySeverity(Enum):
    """The severity of one observed safety event."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclasses.dataclass(frozen=True, slots=True)
class SafetyEvent(BaseEvent):
    """One leading-safety-indicator observation (speed violation, fatigue
    flag, proximity alert, seatbelt non-compliance). Instantaneous by
    nature, so :meth:`duration_h` is always ``0.0``.

    Examples
    --------
    >>> event = SafetyEvent(
    ...     equipment_id="HT-214", shift_id="A-2026-06-25",
    ...     safety_event_type=SafetyEventType.SPEED_VIOLATION,
    ...     severity=SafetySeverity.MEDIUM, zone_id="B7N_CR1",
    ... )
    >>> event.duration_h()
    0.0
    """

    event_type_code: ClassVar[str] = "SAFETY"

    safety_event_type: SafetyEventType
    severity: SafetySeverity
    zone_id: str | None = dataclasses.field(default=None, kw_only=True)

    def duration_h(self) -> float:
        return 0.0
