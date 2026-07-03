"""Tests for mineproductivity.ontology.equipment.fixed_plant."""

from __future__ import annotations

from mineproductivity.ontology.equipment.fixed_plant import Conveyor, Crusher, Mill


class TestCrusher:
    def test_construction(self) -> None:
        crusher = Crusher(id="CR-1", rated_capacity=0.0, throughput_capacity_tph=2500.0)
        assert crusher.throughput_capacity_tph == 2500.0

    def test_supported_kpis(self) -> None:
        assert Crusher.meta.supported_kpis == ("CRUSH.Throughput", "UTIL.OEE", "CRUSH.Utilisation")


class TestConveyor:
    def test_construction(self) -> None:
        conveyor = Conveyor(id="CV-1", rated_capacity=0.0, length_m=850.0)
        assert conveyor.length_m == 850.0

    def test_length_defaults_to_zero(self) -> None:
        conveyor = Conveyor(id="CV-2", rated_capacity=0.0)
        assert conveyor.length_m == 0.0


class TestMill:
    def test_construction(self) -> None:
        mill = Mill(id="ML-1", rated_capacity=0.0, mill_type="sag")
        assert mill.mill_type == "sag"

    def test_mill_type_defaults_to_ball(self) -> None:
        mill = Mill(id="ML-2", rated_capacity=0.0)
        assert mill.mill_type == "ball"
