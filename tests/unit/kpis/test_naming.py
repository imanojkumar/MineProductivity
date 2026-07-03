"""Tests for mineproductivity.kpis.naming."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.exceptions import KPIValidationError
from mineproductivity.kpis.naming import CONTROLLED_NAMESPACES, KPIIdentifier, parse_identifier


class TestControlledNamespaces:
    def test_contains_every_namespace_from_the_design_specification(self) -> None:
        assert CONTROLLED_NAMESPACES == frozenset(
            {
                "PROD",
                "UTIL",
                "MAINT",
                "HAUL",
                "DISP",
                "QUAL",
                "COST",
                "ENERGY",
                "CARBON",
                "WATER",
                "SAFE",
                "AUTO",
                "GRADE",
                "BLEND",
                "CRUSH",
                "PROC",
                "STOCK",
                "RAIL",
                "PORT",
                "TWIN",
                "DI",
                "AI",
            }
        )


class TestParseIdentifier:
    def test_simple_namespace_dot_name(self) -> None:
        identifier = parse_identifier("PROD.TPH")
        assert identifier.namespace == "PROD"
        assert identifier.name == "TPH"
        assert identifier.specialization == ()

    def test_with_one_specialization(self) -> None:
        identifier = parse_identifier("PROD.TPH.Ore")
        assert identifier.specialization == ("Ore",)

    def test_with_multiple_specializations(self) -> None:
        identifier = parse_identifier("PROD.TPH.Ore.North")
        assert identifier.specialization == ("Ore", "North")

    def test_missing_dot_raises(self) -> None:
        with pytest.raises(KPIValidationError):
            parse_identifier("PRODTPH")

    def test_unrecognized_namespace_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="not a recognized KPI namespace"):
            parse_identifier("NOTREAL.Thing")

    def test_lowercase_name_segment_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="PascalCase"):
            parse_identifier("PROD.tph")

    def test_non_alnum_name_segment_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="PascalCase"):
            parse_identifier("PROD.T-PH")

    def test_empty_specialization_segment_raises(self) -> None:
        with pytest.raises(KPIValidationError, match="PascalCase"):
            parse_identifier("PROD.TPH.")


class TestKPIIdentifier:
    def test_str_round_trips_without_specialization(self) -> None:
        identifier = KPIIdentifier(namespace="PROD", name="TPH")
        assert str(identifier) == "PROD.TPH"

    def test_str_round_trips_with_specialization(self) -> None:
        identifier = KPIIdentifier(namespace="PROD", name="TPH", specialization=("Ore",))
        assert str(identifier) == "PROD.TPH.Ore"

    def test_structural_equality(self) -> None:
        assert KPIIdentifier(namespace="PROD", name="TPH") == KPIIdentifier(
            namespace="PROD", name="TPH"
        )

    def test_parse_then_str_is_idempotent(self) -> None:
        for code in ("PROD.TPH", "PROD.TPH.Ore", "UTIL.OEE"):
            assert str(parse_identifier(code)) == code
