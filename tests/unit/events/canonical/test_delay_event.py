"""Tests for mineproductivity.events.canonical.delay_event."""

from __future__ import annotations

import pytest

from mineproductivity.events.canonical import DelayEvent
from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.ontology import DelayCategory


def make_delay(**overrides: object) -> DelayEvent:
    defaults: dict[str, object] = dict(
        equipment_id="CR-01",
        shift_id="A-2026-06-25",
        delay_category=DelayCategory.EQUIPMENT,
        delay_reason="crusher_down",
        duration_min=252.0,
    )
    defaults.update(overrides)
    return DelayEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert DelayEvent.event_type_code == "DELAY"


class TestDurationH:
    def test_converts_minutes_to_hours(self) -> None:
        assert round(make_delay().duration_h(), 2) == 4.2


class TestValidation:
    def test_negative_duration_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_delay(duration_min=-1.0)

    def test_empty_reason_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_delay(delay_reason="")

    def test_whitespace_only_reason_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_delay(delay_reason="   ")

    def test_zero_duration_accepted(self) -> None:
        assert make_delay(duration_min=0.0).duration_min == 0.0


class TestDelayCategoryIntegration:
    @pytest.mark.parametrize("category", list(DelayCategory))
    def test_every_canonical_category_accepted(self, category: DelayCategory) -> None:
        assert make_delay(delay_category=category).delay_category is category

    def test_precedence_accessible(self) -> None:
        assert make_delay(delay_category=DelayCategory.EQUIPMENT).delay_category.precedence == 0
