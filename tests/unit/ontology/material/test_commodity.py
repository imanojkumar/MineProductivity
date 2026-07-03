"""Tests for mineproductivity.ontology.material.commodity."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.material.commodity import Commodity


class TestConstruction:
    def test_valid_construction(self) -> None:
        copper = Commodity(id="copper", symbol="Cu", unit_basis="tonnes")
        assert copper.symbol == "Cu"
        assert copper.unit_basis == "tonnes"


class TestValidation:
    def test_empty_symbol_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Commodity(id="x", symbol="", unit_basis="tonnes")

    def test_empty_unit_basis_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Commodity(id="x", symbol="Cu", unit_basis="")

    def test_whitespace_only_symbol_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Commodity(id="x", symbol="   ", unit_basis="tonnes")
