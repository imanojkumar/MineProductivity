"""Tests for mineproductivity.kpis.standard_library.safety."""

from __future__ import annotations

from mineproductivity.ontology import SafetyEventType

from mineproductivity.kpis.metadata import Direction
from mineproductivity.kpis.standard_library.safety import SpeedViolationCount


class TestSpeedViolationCount:
    def test_code(self) -> None:
        assert SpeedViolationCount.meta.code == "SAFE.SpeedViolationCount"

    def test_lower_is_better(self) -> None:
        assert SpeedViolationCount.meta.direction is Direction.LOWER_IS_BETTER

    def test_counts_only_speed_violations(self) -> None:
        rows = [
            {"safety_event_type": SafetyEventType.SPEED_VIOLATION},
            {"safety_event_type": SafetyEventType.FATIGUE},
            {"safety_event_type": SafetyEventType.SPEED_VIOLATION},
        ]
        result = SpeedViolationCount().compute(rows)
        assert result.value == 2.0

    def test_no_violations_is_a_legitimate_zero(self) -> None:
        rows = [{"safety_event_type": SafetyEventType.FATIGUE}]
        result = SpeedViolationCount().compute(rows)
        assert result.value == 0.0

    def test_uses_the_same_enum_ontology_and_events_share(self) -> None:
        """Proves the earlier SafetyEventType-duplication fix is genuinely
        load-bearing: this KPI's ``_compute`` filters by identity
        (``is``) against ``ontology.SafetyEventType``, so it would
        silently never match anything if ``events.SafetyEvent`` used a
        second, separately-defined enum."""
        from mineproductivity.events import SafetyEventType as EventsSafetyEventType

        assert SafetyEventType is EventsSafetyEventType
