"""Tests for mineproductivity.ontology.equipment.drill."""

from __future__ import annotations

from mineproductivity.ontology.equipment.drill import BlastholeDrill


class TestBlastholeDrill:
    def test_construction(self) -> None:
        drill = BlastholeDrill(id="DR-1", model="PV351", hole_diameter_mm=250.0, rated_capacity=0.0)
        assert drill.model == "PV351"
        assert drill.hole_diameter_mm == 250.0

    def test_hole_diameter_defaults_to_zero(self) -> None:
        drill = BlastholeDrill(id="DR-2", rated_capacity=0.0)
        assert drill.hole_diameter_mm == 0.0

    def test_supported_kpis(self) -> None:
        assert "DRILL.PenetrationRate" in BlastholeDrill.meta.supported_kpis
