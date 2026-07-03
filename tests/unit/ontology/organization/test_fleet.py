"""Tests for mineproductivity.ontology.organization.fleet."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.organization.fleet import Fleet


class TestConstruction:
    def test_valid_construction(self) -> None:
        fleet = Fleet(id="FL-NORTH", mine_id="bingham-west", equipment_type_code="RIGID_HAUL_TRUCK")
        assert fleet.equipment_type_code == "RIGID_HAUL_TRUCK"

    def test_supported_kpis(self) -> None:
        assert Fleet.meta.supported_kpis == ("HAUL.MatchFactor",)


class TestValidation:
    def test_empty_equipment_type_code_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Fleet(id="x", mine_id="bingham-west", equipment_type_code="")
