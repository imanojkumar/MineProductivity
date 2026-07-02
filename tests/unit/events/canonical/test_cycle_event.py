"""Tests for mineproductivity.events.canonical.cycle_event."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.exceptions import EventValidationError


def make_cycle(**overrides: object) -> CycleEvent:
    defaults: dict[str, object] = dict(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        queue_min=1.5,
        spot_min=0.5,
        load_min=2.5,
        haul_min=8.0,
        dump_min=1.0,
        return_min=6.0,
        payload_t=220.0,
    )
    defaults.update(overrides)
    return CycleEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert CycleEvent.event_type_code == "CYCLE"

    def test_optional_fields_default(self) -> None:
        cycle = make_cycle()
        assert cycle.route_id is None
        assert cycle.operator_id is None
        assert cycle.material_type == "unspecified"

    def test_optional_fields_settable(self) -> None:
        cycle = make_cycle(route_id="B7N_CR1", operator_id="OP-001", material_type="Ore")
        assert cycle.route_id == "B7N_CR1"
        assert cycle.operator_id == "OP-001"
        assert cycle.material_type == "Ore"


class TestCycleMin:
    def test_sums_all_six_legs(self) -> None:
        assert make_cycle().cycle_min == 19.5

    def test_worked_example_from_cookbook(self) -> None:
        cycle = make_cycle(
            queue_min=2,
            spot_min=0.5,
            load_min=3,
            haul_min=9,
            dump_min=1.5,
            return_min=6,
            payload_t=200.0,
        )
        assert cycle.cycle_min == 22.0


class TestDurationH:
    def test_converts_minutes_to_hours(self) -> None:
        assert make_cycle().duration_h() == pytest.approx(19.5 / 60.0)


class TestValidation:
    def test_negative_payload_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            make_cycle(payload_t=-1.0)

    def test_zero_payload_accepted(self) -> None:
        assert make_cycle(payload_t=0.0).payload_t == 0.0

    @pytest.mark.parametrize(
        "field", ["queue_min", "spot_min", "load_min", "haul_min", "dump_min", "return_min"]
    )
    def test_negative_leg_rejected(self, field: str) -> None:
        with pytest.raises(EventValidationError):
            make_cycle(**{field: -1.0})


class TestEqualityAndImmutability:
    def test_equal_fields_are_equal(self) -> None:
        assert make_cycle() == make_cycle()

    def test_is_frozen(self) -> None:
        cycle = make_cycle()
        with pytest.raises(dataclasses.FrozenInstanceError):
            cycle.payload_t = 999.0  # type: ignore[misc]
