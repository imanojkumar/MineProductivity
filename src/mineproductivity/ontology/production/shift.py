"""``Shift``, ``ShiftPattern``, ``ShiftCalendar``: the production time-window entities."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from enum import Enum
from typing import ClassVar


from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.entity_type import (
    BaseEntityType,
    EntityTypeMetadata,
    register_entity_type,
)

__all__ = ["Shift", "ShiftCalendar", "ShiftPattern"]


class ShiftPattern(Enum):
    """Common shift patterns mines operate under."""

    TWO_BY_TWELVE = "2x12"  # two 12-hour shifts per day
    THREE_BY_EIGHT = "3x8"  # three 8-hour shifts per day
    FOUR_BY_SIX = "4x6"  # four 6-hour shifts per day
    CUSTOM = "custom"


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Shift(BaseEntityType):
    """One scheduled production shift: a UTC time window plus its
    scheduled-hours denominator (the authoritative basis for
    ``UTIL.PA``/``UTIL.UA`` per the KPI Engine spec's canonical time model).

    Examples
    --------
    >>> from datetime import timezone
    >>> shift = Shift(
    ...     id="A-2026-06-25", mine_id="bingham-west", pattern="2x12",
    ...     start_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
    ...     end_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
    ...     scheduled_h=12.0,
    ... )
    >>> shift.contains(datetime(2026, 6, 25, 7, tzinfo=timezone.utc))
    True
    """

    code: ClassVar[str] = "SHIFT"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Shift",
        description="One scheduled production shift: a UTC time window plus its scheduled hours.",
    )

    mine_id: str
    pattern: str  # "2x12" etc. -- see ShiftPattern for the closed set of common values
    start_utc: datetime
    end_utc: datetime
    scheduled_h: float

    def contains(self, event_time_utc: datetime) -> bool:
        """Half-open interval test: ``start_utc <= t < end_utc`` (the
        Learning & Benchmark Suite's shift-assignment rule)."""
        return self.start_utc <= event_time_utc < self.end_utc

    def validate(self) -> None:
        if self.end_utc <= self.start_utc:
            raise OntologyValidationError("Shift.end_utc must be after start_utc")
        if self.scheduled_h < 0:
            raise OntologyValidationError("Shift.scheduled_h must be >= 0")


@register_entity_type
@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class ShiftCalendar(BaseEntityType):
    """The master shift reference table for one mine (the Learning &
    Benchmark Suite's ``shared/shift_calendar.csv``): declares the
    pattern and timezone convention every :class:`Shift` instance at
    that mine must conform to.
    """

    code: ClassVar[str] = "SHIFT_CALENDAR"
    meta: ClassVar[EntityTypeMetadata] = EntityTypeMetadata(
        name="Shift Calendar",
        description="The master shift reference table for one mine.",
    )

    mine_id: str
    pattern: ShiftPattern
    timezone: str  # IANA timezone name, e.g. "Australia/Perth"

    def validate(self) -> None:
        if not self.timezone.strip():
            raise OntologyValidationError("ShiftCalendar.timezone must not be empty")
