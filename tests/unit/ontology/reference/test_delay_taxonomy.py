"""Tests for mineproductivity.ontology.reference.delay_taxonomy."""

from __future__ import annotations

from mineproductivity.ontology.reference.delay_taxonomy import DelayCategory


class TestDelayCategory:
    def test_has_six_canonical_categories(self) -> None:
        assert len(list(DelayCategory)) == 6

    def test_values(self) -> None:
        assert DelayCategory.SCHEDULED.value == "Scheduled"
        assert DelayCategory.OPERATIONAL.value == "Operational"
        assert DelayCategory.EQUIPMENT.value == "Equipment"
        assert DelayCategory.PROCESS.value == "Process"
        assert DelayCategory.EXTERNAL.value == "External"
        assert DelayCategory.STANDBY.value == "Standby"

    def test_precedence_is_unique_per_category(self) -> None:
        precedences = [category.precedence for category in DelayCategory]
        assert len(precedences) == len(set(precedences))

    def test_equipment_has_highest_precedence(self) -> None:
        assert DelayCategory.EQUIPMENT.precedence == min(c.precedence for c in DelayCategory)

    def test_external_has_lowest_precedence(self) -> None:
        assert DelayCategory.EXTERNAL.precedence == max(c.precedence for c in DelayCategory)
