"""Tests for mineproductivity.ontology.location.pit."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.location.pit import Bench, Pit


class TestPit:
    def test_valid_construction(self) -> None:
        pit = Pit(id="pit-west", mine_id="bingham-west", commodity="copper")
        assert pit.mine_id == "bingham-west"

    def test_empty_mine_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Pit(id="x", mine_id="", commodity="copper")


class TestBench:
    def test_valid_construction(self) -> None:
        bench = Bench(id="bench-7", pit_id="pit-west", elevation_m=1820.0)
        assert bench.elevation_m == 1820.0

    def test_empty_pit_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Bench(id="x", pit_id="", elevation_m=1820.0)
