"""Tests for mineproductivity.events.base_event."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.events.base_event import BaseEvent


class TestBaseEvent:
    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            BaseEvent(equipment_id="E-1", shift_id="S-1")  # type: ignore[abstract]

    def test_subclass_must_implement_duration_h(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True)
        class Incomplete(BaseEvent):
            pass

        with pytest.raises(TypeError):
            Incomplete(equipment_id="E-1", shift_id="S-1")  # type: ignore[abstract]

    def test_concrete_subclass_is_instantiable(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True)
        class Concrete(BaseEvent):
            def duration_h(self) -> float:
                return 1.5

        event = Concrete(equipment_id="E-1", shift_id="S-1")
        assert event.equipment_id == "E-1"
        assert event.shift_id == "S-1"
        assert event.duration_h() == 1.5

    def test_equality_is_by_value_not_identity(self) -> None:
        @dataclasses.dataclass(frozen=True, slots=True)
        class Concrete(BaseEvent):
            def duration_h(self) -> float:
                return 0.0

        assert Concrete(equipment_id="E-1", shift_id="S-1") == Concrete(
            equipment_id="E-1", shift_id="S-1"
        )
        assert Concrete(equipment_id="E-1", shift_id="S-1") != Concrete(
            equipment_id="E-2", shift_id="S-1"
        )
