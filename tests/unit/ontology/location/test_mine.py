"""Tests for mineproductivity.ontology.location.mine."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.location.mine import Mine


class TestConstruction:
    def test_valid_construction(self) -> None:
        mine = Mine(id="bingham-west", commodity_codes=("copper",), method="open_pit")
        assert mine.method == "open_pit"
        assert mine.commodity_codes == ("copper",)

    def test_underground_method(self) -> None:
        mine = Mine(id="deep-south", commodity_codes=("gold",), method="underground")
        assert mine.method == "underground"


class TestValidation:
    def test_empty_commodity_codes_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Mine(id="x", commodity_codes=(), method="open_pit")
