"""Tests for mineproductivity.ontology.location.route."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.location.route import Route, Zone


class TestZone:
    def test_valid_construction(self) -> None:
        zone = Zone(id="B7N_CR1", mine_id="bingham-west", zone_type="haul_road")
        assert zone.zone_type == "haul_road"

    def test_zone_type_defaults_to_general(self) -> None:
        zone = Zone(id="B7N", mine_id="bingham-west")
        assert zone.zone_type == "general"

    def test_empty_mine_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Zone(id="x", mine_id="")


class TestRoute:
    def test_valid_construction(self) -> None:
        route = Route(
            id="B7N_CR1",
            source_zone_id="B7N",
            destination_zone_id="CR1",
            one_way_km=3.2,
            effective_grade_pct=8.5,
        )
        assert route.one_way_km == 3.2

    def test_supported_kpis(self) -> None:
        assert Route.meta.supported_kpis == (
            "HAUL.TonKm",
            "ENERGY.FuelPerTonne",
            "HAUL.EffectiveGrade",
        )

    def test_negative_distance_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Route(
                id="x",
                source_zone_id="A",
                destination_zone_id="B",
                one_way_km=-1.0,
                effective_grade_pct=0.0,
            )
