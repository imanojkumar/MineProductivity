"""Tests for mineproductivity.events.canonical.maintenance_event."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.canonical import MaintenanceEvent
from mineproductivity.events.exceptions import EventValidationError

NOW = datetime(2026, 1, 15, 4, tzinfo=timezone.utc)


def make_maintenance(**overrides: object) -> MaintenanceEvent:
    defaults: dict[str, object] = dict(
        equipment_id="T-101",
        shift_id="PIL_2026-01-15_D",
        failure_start_utc=NOW,
        return_to_service_utc=NOW + timedelta(hours=3),
        total_downtime_h=3.0,
        is_planned=False,
        failure_mode_code="HYD-001",
    )
    defaults.update(overrides)
    return MaintenanceEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert MaintenanceEvent.event_type_code == "MAINTENANCE"


class TestDurationH:
    def test_returns_total_downtime(self) -> None:
        assert make_maintenance().duration_h() == 3.0


class TestValidation:
    def test_negative_downtime_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_maintenance(total_downtime_h=-1.0)

    def test_return_before_failure_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_maintenance(return_to_service_utc=NOW - timedelta(hours=1))

    def test_return_equal_to_failure_accepted(self) -> None:
        event = make_maintenance(return_to_service_utc=NOW, total_downtime_h=0.0)
        assert event.duration_h() == 0.0

    def test_empty_failure_mode_code_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_maintenance(failure_mode_code="")

    def test_is_planned_flag(self) -> None:
        assert make_maintenance(is_planned=True).is_planned is True
