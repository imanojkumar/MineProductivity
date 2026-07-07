"""Tests for mineproductivity.analytics.aggregation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import KPIEngine, KPINotFoundError, KPIResult

from mineproductivity.analytics.aggregation import AggregationEngine, GroupBySpec
from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.result import StatisticalSummary
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint


class TestGroupBySpec:
    def test_by_is_stored(self) -> None:
        spec = GroupBySpec(("pit", "shift"))
        assert spec.by == ("pit", "shift")

    def test_equality_is_value_based(self) -> None:
        assert GroupBySpec(("pit",)) == GroupBySpec(("pit",))
        assert GroupBySpec(("pit",)) != GroupBySpec(("shift",))
        assert GroupBySpec(("pit",)) != "not a GroupBySpec"

    def test_hashable_and_consistent_with_equality(self) -> None:
        assert hash(GroupBySpec(("pit",))) == hash(GroupBySpec(("pit",)))

    def test_repr(self) -> None:
        assert repr(GroupBySpec(("pit",))) == "GroupBySpec(by=('pit',))"


class TestAggregationEngineReduce:
    _START = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def _point(self, value: float, *, day: int = 0, scope: dict[str, str]) -> TimeSeriesPoint:
        return TimeSeriesPoint(
            timestamp=self._START + timedelta(days=day), value=value, scope=scope
        )

    def test_groups_by_the_named_scope_field(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(10.0, day=0, scope={"pit": "north"}),
                self._point(20.0, day=1, scope={"pit": "north"}),
                self._point(30.0, day=2, scope={"pit": "south"}),
            )
        )
        groups = engine.reduce(series, GroupBySpec(("pit",)), reduction="mean")
        assert set(groups) == {("north",), ("south",)}
        assert isinstance(groups[("north",)], StatisticalSummary)

    def test_points_missing_a_grouped_field_are_excluded_from_every_group(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(10.0, day=0, scope={"pit": "north"}),
                self._point(999.0, day=1, scope={}),  # no "pit" -- cannot be classified
            )
        )
        groups = engine.reduce(series, GroupBySpec(("pit",)), reduction="mean")
        assert set(groups) == {("north",)}
        summary = groups[("north",)]
        assert isinstance(summary, StatisticalSummary)
        assert summary.n == 1

    def test_empty_series_produces_no_groups(self) -> None:
        engine = AggregationEngine()
        groups = engine.reduce(TimeSeries(points=()), GroupBySpec(("pit",)), reduction="mean")
        assert groups == {}

    def test_mean_reduction_matches_the_groups_own_statistical_summary_mean(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(10.0, day=0, scope={"pit": "north"}),
                self._point(20.0, day=1, scope={"pit": "north"}),
            )
        )
        summary = engine.reduce(series, GroupBySpec(("pit",)), reduction="mean")[("north",)]
        assert isinstance(summary, StatisticalSummary)
        assert summary.mean == 15.0

    def test_median_reduction_is_the_50th_percentile(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(1.0, day=0, scope={"pit": "north"}),
                self._point(2.0, day=1, scope={"pit": "north"}),
                self._point(3.0, day=2, scope={"pit": "north"}),
            )
        )
        summary = engine.reduce(series, GroupBySpec(("pit",)), reduction="median")[("north",)]
        assert isinstance(summary, StatisticalSummary)
        assert summary.percentiles[50] == 2.0

    def test_sum_reduction_is_derivable_as_mean_times_n(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(10.0, day=0, scope={"pit": "north"}),
                self._point(20.0, day=1, scope={"pit": "north"}),
                self._point(30.0, day=2, scope={"pit": "north"}),
            )
        )
        summary = engine.reduce(series, GroupBySpec(("pit",)), reduction="sum")[("north",)]
        assert isinstance(summary, StatisticalSummary)
        assert summary.mean * summary.n == pytest.approx(60.0)

    def test_grouping_by_multiple_fields_produces_a_composite_key(self) -> None:
        engine = AggregationEngine()
        series = TimeSeries(
            points=(
                self._point(1.0, day=0, scope={"pit": "north", "shift": "A"}),
                self._point(2.0, day=1, scope={"pit": "north", "shift": "B"}),
            )
        )
        groups = engine.reduce(series, GroupBySpec(("pit", "shift")), reduction="mean")
        assert set(groups) == {("north", "A"), ("north", "B")}


class TestReduceKpiResultsValidation:
    def test_empty_results_raises(self, engine: KPIEngine) -> None:
        agg = AggregationEngine()
        with pytest.raises(AnalyticsValidationError, match="at least one"):
            agg.reduce_kpi_results([], engine=engine, window="shift", combined_scope={})

    def test_mixed_codes_raises(self, engine: KPIEngine) -> None:
        agg = AggregationEngine()
        results = [
            KPIResult(code="PROD.TPH", value=1.0, unit="t/h"),
            KPIResult(code="ENERGY.FuelConsumed", value=2.0, unit="L"),
        ]
        with pytest.raises(AnalyticsValidationError, match="same code"):
            agg.reduce_kpi_results(results, engine=engine, window="shift", combined_scope={})

    def test_unregistered_code_returns_err(self, engine: KPIEngine) -> None:
        agg = AggregationEngine()
        results = [KPIResult(code="NOTREAL.Thing", value=1.0, unit="x")]
        outcome = agg.reduce_kpi_results(results, engine=engine, window="shift", combined_scope={})
        assert outcome.is_err
        assert isinstance(outcome.error, KPINotFoundError)


class TestReduceKpiResultsAdditive:
    """``ENERGY.FuelConsumed`` is a real, already-registered ``ADDITIVE``
    KPI -- the direct-sum path never touches ``engine``/the event store,
    so plain ``KPIResult`` fixtures are enough to exercise it."""

    def test_direct_sum_of_additive_kpi(self, engine: KPIEngine) -> None:
        agg = AggregationEngine()
        results = [
            KPIResult(code="ENERGY.FuelConsumed", value=100.0, unit="L", n=5, scope={"shift": "A"}),
            KPIResult(code="ENERGY.FuelConsumed", value=50.0, unit="L", n=3, scope={"shift": "B"}),
        ]
        outcome = agg.reduce_kpi_results(
            results, engine=engine, window="day", combined_scope={"day": "2026-06-25"}
        )
        assert outcome.is_ok
        combined = outcome.unwrap()
        assert combined.code == "ENERGY.FuelConsumed"
        assert combined.value == 150.0
        assert combined.n == 8
        assert combined.scope == {"day": "2026-06-25"}
        assert combined.warnings == ()

    def test_direct_sum_propagates_none_when_any_input_is_uncomputable(
        self, engine: KPIEngine
    ) -> None:
        agg = AggregationEngine()
        results = [
            KPIResult(code="ENERGY.FuelConsumed", value=100.0, unit="L", n=5),
            KPIResult(code="ENERGY.FuelConsumed", value=None, unit="L", n=0),
        ]
        outcome = agg.reduce_kpi_results(results, engine=engine, window="day", combined_scope={})
        assert outcome.is_ok
        combined = outcome.unwrap()
        assert combined.value is None
        assert len(combined.warnings) == 1

    def test_direct_sum_of_a_single_result_is_that_results_own_value(
        self, engine: KPIEngine
    ) -> None:
        agg = AggregationEngine()
        results = [KPIResult(code="ENERGY.FuelConsumed", value=42.0, unit="L", n=1)]
        outcome = agg.reduce_kpi_results(results, engine=engine, window="day", combined_scope={})
        assert outcome.unwrap().value == 42.0


class TestReduceKpiResultsRatio:
    """``PROD.TPH`` is a real, already-registered ``RATIO`` KPI -- proves
    the "never average an already-computed ratio" rule (design spec
    §10, §34): the correct combined TPH re-derives from the summed
    payload/summed hours over the union scope, never the naive average
    of the two shifts' own TPH values."""

    def _cycle(
        self, cycle_event_factory: Callable[..., CycleEvent], *, shift_id: str, payload_t: float
    ) -> CycleEvent:
        return cycle_event_factory(shift_id=shift_id, payload_t=payload_t)

    def _append(
        self,
        event_store: _InMemoryEventStore,
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
        payload: CycleEvent,
    ) -> None:
        result = event_store.append(cycle_envelope_factory(payload=payload))
        assert result.is_ok

    def test_ratio_kpi_delegates_to_engine_execute_over_combined_scope(
        self,
        engine: KPIEngine,
        event_store: _InMemoryEventStore,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        # Shift A: 2 cycles of 220.0 t each (0.325 h/cycle -> 0.65 h, 440.0 t).
        for _ in range(2):
            self._append(
                event_store,
                cycle_envelope_factory,
                self._cycle(cycle_event_factory, shift_id="A-shift", payload_t=220.0),
            )
        # Shift B: 3 cycles of 100.0 t each (0.325 h/cycle -> 0.975 h, 300.0 t).
        for _ in range(3):
            self._append(
                event_store,
                cycle_envelope_factory,
                self._cycle(cycle_event_factory, shift_id="B-shift", payload_t=100.0),
            )

        result_a = engine.execute("PROD.TPH", window="shift", scope={"shift": "A-shift"}).unwrap()
        result_b = engine.execute("PROD.TPH", window="shift", scope={"shift": "B-shift"}).unwrap()
        naive_average = (result_a.value + result_b.value) / 2  # type: ignore[operator]

        agg = AggregationEngine()
        combined = agg.reduce_kpi_results(
            [result_a, result_b], engine=engine, window="day", combined_scope={}
        ).unwrap()

        # Correct: (440.0 + 300.0) / (0.65 + 0.975) = 740.0 / 1.625.
        assert combined.value == pytest.approx(740.0 / 1.625)
        assert combined.value != pytest.approx(naive_average)

    def test_ratio_kpi_result_is_still_a_kpi_result(self, engine: KPIEngine) -> None:
        agg = AggregationEngine()
        results = [KPIResult(code="PROD.TPH", value=100.0, unit="t/h")]
        # A single-element RATIO reduction re-executes over combined_scope;
        # with no matching events, engine.execute legitimately returns None.
        outcome = agg.reduce_kpi_results(
            results, engine=engine, window="day", combined_scope={"day": "2026-06-25"}
        )
        assert outcome.is_ok
        assert isinstance(outcome.unwrap(), KPIResult)


class TestAggregationEngineConstruction:
    def test_constructs_without_a_backend(self) -> None:
        AggregationEngine()  # must not raise

    def test_constructs_with_an_explicit_backend(self) -> None:
        from mineproductivity.kpis.backends import PandasBackend

        AggregationEngine(backend=PandasBackend())  # must not raise
