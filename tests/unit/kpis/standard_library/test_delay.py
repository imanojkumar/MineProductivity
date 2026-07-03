"""Tests for mineproductivity.kpis.standard_library.delay."""

from __future__ import annotations

from mineproductivity.kpis.metadata import Aggregation
from mineproductivity.kpis.standard_library.delay import TotalDelayHours


class TestTotalDelayHours:
    def test_code(self) -> None:
        assert TotalDelayHours.meta.code == "DISP.TotalDelayHours"

    def test_aggregation_is_additive(self) -> None:
        assert TotalDelayHours.meta.aggregation is Aggregation.ADDITIVE

    def test_sums_duration_h_across_rows(self) -> None:
        result = TotalDelayHours().compute([{"duration_h": 2.0}, {"duration_h": 1.5}])
        assert result.value == 3.5

    def test_empty_window_is_a_legitimate_zero_not_none(self) -> None:
        result = TotalDelayHours().compute([])
        assert result.value == 0.0
