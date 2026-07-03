"""Tests for mineproductivity.kpis.standard_library.quality."""

from __future__ import annotations

from mineproductivity.kpis.metadata import Direction
from mineproductivity.kpis.standard_library.quality import OreProportion


class TestOreProportion:
    def test_code(self) -> None:
        assert OreProportion.meta.code == "QUAL.OreProportion"

    def test_target_is_best_direction(self) -> None:
        assert OreProportion.meta.direction is Direction.TARGET_IS_BEST

    def test_ratio_of_ore_to_all_cycles(self) -> None:
        rows = [
            {"material_type": "ore"},
            {"material_type": "waste"},
            {"material_type": "ore"},
        ]
        result = OreProportion().compute(rows)
        assert result.value == 2 / 3

    def test_all_ore(self) -> None:
        result = OreProportion().compute([{"material_type": "ore"}, {"material_type": "ore"}])
        assert result.value == 1.0

    def test_all_waste(self) -> None:
        result = OreProportion().compute([{"material_type": "waste"}])
        assert result.value == 0.0

    def test_zero_cycles_returns_none(self) -> None:
        result = OreProportion().compute([])
        assert result.value is None
