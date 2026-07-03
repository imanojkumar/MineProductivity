"""Tests for mineproductivity.ontology.production.shift."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.production.shift import Shift, ShiftCalendar, ShiftPattern


def make_shift(**overrides: object) -> Shift:
    defaults: dict[str, object] = dict(
        id="A-2026-06-25",
        mine_id="bingham-west",
        pattern="2x12",
        start_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
        end_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
        scheduled_h=12.0,
    )
    defaults.update(overrides)
    return Shift(**defaults)  # type: ignore[arg-type]


class TestShiftPattern:
    def test_has_four_patterns(self) -> None:
        assert len(list(ShiftPattern)) == 4

    def test_values(self) -> None:
        assert ShiftPattern.TWO_BY_TWELVE.value == "2x12"
        assert ShiftPattern.THREE_BY_EIGHT.value == "3x8"
        assert ShiftPattern.FOUR_BY_SIX.value == "4x6"
        assert ShiftPattern.CUSTOM.value == "custom"


class TestShiftConstruction:
    def test_valid_construction(self) -> None:
        shift = make_shift()
        assert shift.scheduled_h == 12.0


class TestShiftContains:
    def test_time_inside_window(self) -> None:
        shift = make_shift()
        assert shift.contains(datetime(2026, 6, 25, 7, tzinfo=timezone.utc)) is True

    def test_start_boundary_is_inclusive(self) -> None:
        shift = make_shift()
        assert shift.contains(datetime(2026, 6, 25, 6, tzinfo=timezone.utc)) is True

    def test_end_boundary_is_exclusive(self) -> None:
        shift = make_shift()
        assert shift.contains(datetime(2026, 6, 25, 18, tzinfo=timezone.utc)) is False

    def test_time_before_window(self) -> None:
        shift = make_shift()
        assert shift.contains(datetime(2026, 6, 25, 5, tzinfo=timezone.utc)) is False


class TestShiftValidation:
    def test_end_before_start_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            make_shift(
                start_utc=datetime(2026, 6, 25, 18, tzinfo=timezone.utc),
                end_utc=datetime(2026, 6, 25, 6, tzinfo=timezone.utc),
            )

    def test_end_equal_start_rejected(self) -> None:
        same = datetime(2026, 6, 25, 6, tzinfo=timezone.utc)
        with pytest.raises(OntologyValidationError):
            make_shift(start_utc=same, end_utc=same)

    def test_negative_scheduled_hours_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            make_shift(scheduled_h=-1.0)


class TestShiftCalendar:
    def test_valid_construction(self) -> None:
        cal = ShiftCalendar(
            id="CAL-1",
            mine_id="bingham-west",
            pattern=ShiftPattern.TWO_BY_TWELVE,
            timezone="Australia/Perth",
        )
        assert cal.pattern is ShiftPattern.TWO_BY_TWELVE
        assert cal.timezone == "Australia/Perth"

    def test_empty_timezone_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            ShiftCalendar(
                id="x", mine_id="bingham-west", pattern=ShiftPattern.TWO_BY_TWELVE, timezone=""
            )
