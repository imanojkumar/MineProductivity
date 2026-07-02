"""Tests for mineproductivity.events.canonical.safety_event."""

from __future__ import annotations

import dataclasses

import pytest

from mineproductivity.events.canonical import SafetyEvent, SafetyEventType, SafetySeverity


def make_safety(**overrides: object) -> SafetyEvent:
    defaults: dict[str, object] = dict(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        safety_event_type=SafetyEventType.SPEED_VIOLATION,
        severity=SafetySeverity.MEDIUM,
    )
    defaults.update(overrides)
    return SafetyEvent(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_event_type_code(self) -> None:
        assert SafetyEvent.event_type_code == "SAFETY"

    def test_zone_id_defaults_to_none(self) -> None:
        assert make_safety().zone_id is None

    def test_zone_id_settable(self) -> None:
        assert make_safety(zone_id="B7N_CR1").zone_id == "B7N_CR1"


class TestDurationH:
    def test_instantaneous_events_have_zero_duration(self) -> None:
        assert make_safety().duration_h() == 0.0


class TestEnums:
    @pytest.mark.parametrize("event_type", list(SafetyEventType))
    def test_every_safety_event_type_accepted(self, event_type: SafetyEventType) -> None:
        assert make_safety(safety_event_type=event_type).safety_event_type is event_type

    @pytest.mark.parametrize("severity", list(SafetySeverity))
    def test_every_severity_accepted(self, severity: SafetySeverity) -> None:
        assert make_safety(severity=severity).severity is severity


class TestImmutability:
    def test_is_frozen(self) -> None:
        event = make_safety()
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.severity = SafetySeverity.CRITICAL  # type: ignore[misc]
