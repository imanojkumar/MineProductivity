"""Tests for mineproductivity.events.canonical.production_event."""

from __future__ import annotations

import pytest

from mineproductivity.events.canonical import ProductionEvent
from mineproductivity.events.exceptions import EventValidationError


def make_production(**overrides: object) -> ProductionEvent:
    defaults: dict[str, object] = dict(
        equipment_id="PIT-NORTH",
        shift_id="PIL_2026-01-15_D",
        pit_code="PIT-NORTH",
        material_type="Ore",
        tonnes_moved=38400.0,
        planned_tonnes=40000.0,
        operating_h=29.7,
    )
    defaults.update(overrides)
    return ProductionEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert ProductionEvent.event_type_code == "PRODUCTION"


class TestDurationH:
    def test_returns_operating_hours(self) -> None:
        assert make_production().duration_h() == 29.7


class TestValidation:
    def test_negative_tonnes_moved_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_production(tonnes_moved=-1.0)

    def test_negative_planned_tonnes_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_production(planned_tonnes=-1.0)

    def test_negative_operating_hours_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_production(operating_h=-1.0)

    def test_zero_values_accepted(self) -> None:
        event = make_production(tonnes_moved=0.0, planned_tonnes=0.0, operating_h=0.0)
        assert event.duration_h() == 0.0
