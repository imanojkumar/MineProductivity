"""Tests for mineproductivity.kpis.aggregation."""

from __future__ import annotations

import pytest

from mineproductivity.kpis.aggregation import combine_results
from mineproductivity.kpis.exceptions import KPIAggregationError
from mineproductivity.kpis.metadata import Aggregation
from mineproductivity.kpis.result import KPIResult


class TestNeverCombineAlreadyComputedRatios:
    @pytest.mark.parametrize(
        "aggregation", [Aggregation.RATIO, Aggregation.AVERAGE, Aggregation.WEIGHTED_AVERAGE]
    )
    def test_raises_for_ratio_kind_aggregations(self, aggregation: Aggregation) -> None:
        results = [
            KPIResult(code="X", value=1300.0, unit="t/h"),
            KPIResult(code="X", value=1100.0, unit="t/h"),
        ]
        with pytest.raises(KPIAggregationError, match="averaging"):
            combine_results(results, aggregation, code="X", unit="t/h")

    def test_ratio_never_averaged_regression_cookbook_ch6_worked_numbers(self) -> None:
        """Design spec §37.2's own acceptance-criteria proof: A-shift 1,300
        t/h over 12h + B-shift 1,100 t/h over 6h combine to 1,233 t/h, not
        the naive 1,200 average -- proven here by asserting the engine
        REFUSES to average already-computed per-shift results at all,
        forcing re-derivation from raw rows (see
        test_engine.py::TestRatioNeverAveraged for the row-level proof)."""
        results = [
            KPIResult(code="PROD.TPH", value=1300.0, unit="t/h", n=1),
            KPIResult(code="PROD.TPH", value=1100.0, unit="t/h", n=1),
        ]
        with pytest.raises(KPIAggregationError):
            combine_results(results, Aggregation.RATIO, code="PROD.TPH", unit="t/h")


class TestDerivedRejected:
    def test_derived_raises_directing_to_composite_kpi(self) -> None:
        results = [KPIResult(code="X", value=1.0, unit="u")]
        with pytest.raises(KPIAggregationError, match="CompositeKPI"):
            combine_results(results, Aggregation.DERIVED, code="X", unit="u")


class TestAdditiveCumulativeRollingSum:
    @pytest.mark.parametrize(
        "aggregation", [Aggregation.ADDITIVE, Aggregation.CUMULATIVE, Aggregation.ROLLING]
    )
    def test_sums_values_and_ns(self, aggregation: Aggregation) -> None:
        results = [
            KPIResult(code="X", value=1.0, unit="u", n=5),
            KPIResult(code="X", value=2.0, unit="u", n=3),
        ]
        combined = combine_results(results, aggregation, code="X", unit="u")
        assert combined.value == 3.0
        assert combined.n == 8
        assert combined.code == "X"
        assert combined.unit == "u"

    def test_none_valued_results_are_skipped_not_treated_as_zero_failure(self) -> None:
        results = [
            KPIResult(code="X", value=None, unit="u", n=0, warnings=("no data",)),
            KPIResult(code="X", value=5.0, unit="u", n=2),
        ]
        combined = combine_results(results, Aggregation.ADDITIVE, code="X", unit="u")
        assert combined.value == 5.0
        assert combined.n == 2

    def test_all_none_results_produce_none_with_a_warning(self) -> None:
        results = [
            KPIResult(code="X", value=None, unit="u"),
            KPIResult(code="X", value=None, unit="u"),
        ]
        combined = combine_results(results, Aggregation.ADDITIVE, code="X", unit="u")
        assert combined.value is None
        assert combined.warnings == ("no combinable values",)

    def test_empty_results_sequence_produces_none(self) -> None:
        combined = combine_results([], Aggregation.ADDITIVE, code="X", unit="u")
        assert combined.value is None
