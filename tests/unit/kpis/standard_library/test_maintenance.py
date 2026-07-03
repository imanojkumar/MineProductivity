"""Tests for mineproductivity.kpis.standard_library.maintenance."""

from __future__ import annotations

from mineproductivity.kpis.metadata import Direction
from mineproductivity.kpis.standard_library.maintenance import MeanTimeToRepair


class TestMeanTimeToRepair:
    def test_code(self) -> None:
        assert MeanTimeToRepair.meta.code == "MAINT.MTTR"

    def test_lower_is_better(self) -> None:
        assert MeanTimeToRepair.meta.direction is Direction.LOWER_IS_BETTER

    def test_mean_of_downtime_hours(self) -> None:
        result = MeanTimeToRepair().compute([{"duration_h": 3.0}, {"duration_h": 5.0}])
        assert result.value == 4.0

    def test_single_failure(self) -> None:
        result = MeanTimeToRepair().compute([{"duration_h": 7.5}])
        assert result.value == 7.5

    def test_zero_failures_returns_none(self) -> None:
        result = MeanTimeToRepair().compute([])
        assert result.value is None
