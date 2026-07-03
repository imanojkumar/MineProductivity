"""Tests for mineproductivity.ontology.equipment.loading_unit."""

from __future__ import annotations

from mineproductivity.ontology.equipment.loading_unit import LHD, HydraulicShovel, WheelLoader


class TestHydraulicShovel:
    def test_construction(self) -> None:
        shovel = HydraulicShovel(id="SH-1", model="EX8000", fleet_id="FL-2", rated_capacity=42.0)
        assert shovel.model == "EX8000"
        assert shovel.rated_capacity == 42.0

    def test_supported_kpis(self) -> None:
        assert "HAUL.MatchFactor" in HydraulicShovel.meta.supported_kpis


class TestWheelLoader:
    def test_construction(self) -> None:
        loader = WheelLoader(id="WL-1", model="994K", rated_capacity=18.0)
        assert loader.model == "994K"

    def test_default_model_is_empty_string(self) -> None:
        loader = WheelLoader(id="WL-2", rated_capacity=1.0)
        assert loader.model == ""


class TestLHD:
    def test_construction(self) -> None:
        lhd = LHD(id="LHD-1", model="R1700", fleet_id="FL-4", rated_capacity=17.0)
        assert lhd.model == "R1700"

    def test_supported_kpis(self) -> None:
        assert "PROD.TruckCycleTime" in LHD.meta.supported_kpis
