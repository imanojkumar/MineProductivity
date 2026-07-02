"""Tests for mineproductivity.events.canonical.consumption_event."""

from __future__ import annotations

import pytest

from mineproductivity.events.canonical import ConsumptionEvent, ResourceType
from mineproductivity.events.exceptions import EventValidationError


def make_consumption(**overrides: object) -> ConsumptionEvent:
    defaults: dict[str, object] = dict(
        equipment_id="T-101",
        shift_id="PIL_2026-01-15_D",
        resource_type=ResourceType.FUEL,
        quantity=1840.0,
        unit="L",
    )
    defaults.update(overrides)
    return ConsumptionEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert ConsumptionEvent.event_type_code == "CONSUMPTION"


class TestDurationH:
    def test_instantaneous_events_have_zero_duration(self) -> None:
        assert make_consumption().duration_h() == 0.0


class TestResourceTypeEnum:
    @pytest.mark.parametrize("resource_type", list(ResourceType))
    def test_every_resource_type_accepted(self, resource_type: ResourceType) -> None:
        assert make_consumption(resource_type=resource_type).resource_type is resource_type


class TestValidation:
    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_consumption(quantity=-1.0)

    def test_empty_unit_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_consumption(unit="")

    def test_zero_quantity_accepted(self) -> None:
        assert make_consumption(quantity=0.0).quantity == 0.0
