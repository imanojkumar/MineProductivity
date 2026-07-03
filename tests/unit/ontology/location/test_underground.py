"""Tests for mineproductivity.ontology.location.underground."""

from __future__ import annotations

import pytest

from mineproductivity.ontology.exceptions import OntologyValidationError
from mineproductivity.ontology.location.underground import Drive, Level, Stope


class TestLevel:
    def test_valid_construction(self) -> None:
        level = Level(id="L-1050", mine_id="bingham-west", elevation_m=1050.0)
        assert level.elevation_m == 1050.0

    def test_parent_code_is_bench(self) -> None:
        assert Level.meta.parent_code == "BENCH"

    def test_empty_mine_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Level(id="x", mine_id="", elevation_m=1050.0)


class TestStope:
    def test_valid_construction(self) -> None:
        stope = Stope(id="ST-1", level_id="L-1050", mining_method="sublevel_stoping")
        assert stope.mining_method == "sublevel_stoping"

    def test_mining_method_defaults_to_empty_string(self) -> None:
        stope = Stope(id="ST-2", level_id="L-1050")
        assert stope.mining_method == ""

    def test_empty_level_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Stope(id="x", level_id="")


class TestDrive:
    def test_valid_construction(self) -> None:
        drive = Drive(id="DR-1", level_id="L-1050", length_m=320.0)
        assert drive.length_m == 320.0

    def test_length_defaults_to_zero(self) -> None:
        drive = Drive(id="DR-2", level_id="L-1050")
        assert drive.length_m == 0.0

    def test_empty_level_id_rejected(self) -> None:
        with pytest.raises(OntologyValidationError):
            Drive(id="x", level_id="")
