"""``MaintenanceEvent``: one unplanned-or-planned equipment failure/repair event."""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import ClassVar

from mineproductivity.events.base_event import BaseEvent
from mineproductivity.events.exceptions import EventValidationError

__all__ = ["MaintenanceEvent"]


@dataclasses.dataclass(frozen=True, slots=True)
class MaintenanceEvent(BaseEvent):
    """One equipment failure event, from failure to return-to-service.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> event = MaintenanceEvent(
    ...     equipment_id="T-101", shift_id="PIL_2026-01-15_D",
    ...     failure_start_utc=datetime(2026, 1, 15, 4, tzinfo=timezone.utc),
    ...     return_to_service_utc=datetime(2026, 1, 15, 7, tzinfo=timezone.utc),
    ...     total_downtime_h=3.0, is_planned=False, failure_mode_code="HYD-001",
    ... )
    >>> event.duration_h()
    3.0
    """

    event_type_code: ClassVar[str] = "MAINTENANCE"

    failure_start_utc: datetime
    return_to_service_utc: datetime
    total_downtime_h: float
    is_planned: bool
    failure_mode_code: str

    def duration_h(self) -> float:
        return self.total_downtime_h

    def validate(self) -> None:
        if self.total_downtime_h < 0:
            raise EventValidationError("MaintenanceEvent.total_downtime_h must be >= 0")
        if self.return_to_service_utc < self.failure_start_utc:
            raise EventValidationError(
                "MaintenanceEvent.return_to_service_utc must be >= failure_start_utc"
            )
        if not self.failure_mode_code.strip():
            raise EventValidationError("MaintenanceEvent.failure_mode_code must not be empty")
