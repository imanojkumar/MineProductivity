"""Tests for mineproductivity.ontology.organization.crew."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.organization.crew import Crew, Operator


class TestCrew:
    def test_valid_construction(self) -> None:
        crew = Crew(id="A", mine_id="bingham-west")
        assert crew.mine_id == "bingham-west"

    def test_empty_mine_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Crew(id="x", mine_id="")


class TestOperator:
    def test_valid_construction(self) -> None:
        operator = Operator(id="OP-001", crew_id="A", licence_class="Haul Truck")
        assert operator.licence_class == "Haul Truck"

    def test_empty_crew_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Operator(id="x", crew_id="", licence_class="Haul Truck")
