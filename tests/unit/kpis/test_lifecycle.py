"""Tests for mineproductivity.kpis.lifecycle."""

from __future__ import annotations

from mineproductivity.kpis.lifecycle import KPIStatus


class TestKPIStatus:
    def test_members(self) -> None:
        assert {member.value for member in KPIStatus} == {
            "proposed",
            "active",
            "deprecated",
            "retired",
        }

    def test_proposed_to_retired_progression_order(self) -> None:
        assert KPIStatus.PROPOSED.value == "proposed"
        assert KPIStatus.ACTIVE.value == "active"
        assert KPIStatus.DEPRECATED.value == "deprecated"
        assert KPIStatus.RETIRED.value == "retired"
