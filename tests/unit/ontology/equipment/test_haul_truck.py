"""Tests for mineproductivity.ontology.equipment.haul_truck."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.equipment.haul_truck import ArticulatedHaulTruck, RigidHaulTruck
from mineproductivity.ontology.exceptions import OntologyValidationError


class TestRigidHaulTruck:
    def test_construction(self) -> None:
        truck = RigidHaulTruck(
            id="HT-214", model="CAT 797F", fleet_id="FL-NORTH", rated_capacity=363.0
        )
        assert truck.model == "CAT 797F"
        assert truck.fuel_type == "diesel"
        assert truck.fleet_id == "FL-NORTH"

    def test_supported_kpis(self) -> None:
        assert RigidHaulTruck.meta.supported_kpis == (
            "PROD.TruckCycleTime",
            "PROD.Payload",
            "UTIL.PA",
            "UTIL.UA",
            "HAUL.TKPH",
            "HAUL.MatchFactor",
        )

    def test_fleet_id_optional(self) -> None:
        truck = RigidHaulTruck(id="HT-1", rated_capacity=1.0)
        assert truck.fleet_id is None

    def test_negative_capacity_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            RigidHaulTruck(id="HT-2", rated_capacity=-1.0)


class TestArticulatedHaulTruck:
    def test_construction(self) -> None:
        truck = ArticulatedHaulTruck(id="AHT-1", model="A45G", fleet_id="FL-1", rated_capacity=41.0)
        assert truck.model == "A45G"
        assert truck.fuel_type == "diesel"

    def test_supported_kpis(self) -> None:
        assert ArticulatedHaulTruck.meta.supported_kpis == (
            "PROD.TruckCycleTime",
            "PROD.Payload",
            "UTIL.PA",
            "UTIL.UA",
        )
