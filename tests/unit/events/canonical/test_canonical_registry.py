"""Tests for mineproductivity.events.canonical's internal type registry."""

from __future__ import annotations

from mineproductivity.events.canonical import (
    ConsumptionEvent,
    CycleEvent,
    DelayEvent,
    MaintenanceEvent,
    ProductionEvent,
    SafetyEvent,
    canonical_event_types,
)


class TestCanonicalEventTypes:
    def test_contains_all_six_canonical_types(self) -> None:
        registry = canonical_event_types()
        assert set(registry.keys()) == {
            "CYCLE",
            "DELAY",
            "MAINTENANCE",
            "PRODUCTION",
            "CONSUMPTION",
            "SAFETY",
        }

    def test_maps_to_correct_classes(self) -> None:
        registry = canonical_event_types()
        assert registry["CYCLE"] is CycleEvent
        assert registry["DELAY"] is DelayEvent
        assert registry["MAINTENANCE"] is MaintenanceEvent
        assert registry["PRODUCTION"] is ProductionEvent
        assert registry["CONSUMPTION"] is ConsumptionEvent
        assert registry["SAFETY"] is SafetyEvent

    def test_keys_match_each_types_own_event_type_code(self) -> None:
        registry = canonical_event_types()
        for code, cls in registry.items():
            assert cls.event_type_code == code
