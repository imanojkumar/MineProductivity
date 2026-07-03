"""Tests for mineproductivity.ontology.equipment.ancillary."""

from __future__ import annotations

from mineproductivity.ontology.equipment.ancillary import Dozer, Grader, WaterTruck


class TestDozer:
    def test_construction(self) -> None:
        dozer = Dozer(id="DZ-1", model="D11T", rated_capacity=0.0)
        assert dozer.model == "D11T"


class TestGrader:
    def test_construction(self) -> None:
        grader = Grader(id="GR-1", model="24M", rated_capacity=0.0)
        assert grader.model == "24M"


class TestWaterTruck:
    def test_construction(self) -> None:
        truck = WaterTruck(id="WT-1", model="777G", tank_capacity_l=60000.0, rated_capacity=90.0)
        assert truck.tank_capacity_l == 60000.0

    def test_tank_capacity_defaults_to_zero(self) -> None:
        truck = WaterTruck(id="WT-2", rated_capacity=1.0)
        assert truck.tank_capacity_l == 0.0

    def test_supported_kpis_match_cookbook_example(self) -> None:
        assert WaterTruck.meta.supported_kpis == ("UTIL.PA", "UTIL.UA", "COST.FuelPerTonne")
