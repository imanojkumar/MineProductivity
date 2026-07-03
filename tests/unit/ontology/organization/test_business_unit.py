"""Tests for mineproductivity.ontology.organization.business_unit."""

from __future__ import annotations

from mineproductivity.ontology.organization.business_unit import BusinessUnit, Contractor


class TestBusinessUnit:
    def test_construction_without_parent(self) -> None:
        bu = BusinessUnit(id="BU-COPPER")
        assert bu.parent_business_unit_id is None

    def test_construction_with_parent(self) -> None:
        bu = BusinessUnit(id="BU-COPPER-WEST", parent_business_unit_id="BU-COPPER")
        assert bu.parent_business_unit_id == "BU-COPPER"


class TestContractor:
    def test_construction(self) -> None:
        contractor = Contractor(id="CON-1", service_type="drill_and_blast")
        assert contractor.service_type == "drill_and_blast"

    def test_service_type_defaults_to_empty_string(self) -> None:
        contractor = Contractor(id="CON-2")
        assert contractor.service_type == ""
