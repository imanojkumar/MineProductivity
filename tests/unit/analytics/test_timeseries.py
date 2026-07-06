"""Tests for mineproductivity.analytics.timeseries."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

import pytest

from mineproductivity.events import EventQuery
from mineproductivity.events.canonical import CycleEvent
from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.store import _InMemoryEventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.analytics.exceptions import AnalyticsValidationError
from mineproductivity.analytics.timeseries import TimeSeries, TimeSeriesPoint

DAY_1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
DAY_2 = datetime(2026, 1, 2, tzinfo=timezone.utc)
DAY_3 = datetime(2026, 1, 3, tzinfo=timezone.utc)


class TestTimeSeriesPoint:
    def test_construction(self) -> None:
        point = TimeSeriesPoint(timestamp=DAY_1, value=1200.0, scope={"pit": "north"})
        assert point.value == 1200.0
        assert point.scope["pit"] == "north"

    def test_scope_defaults_to_empty(self) -> None:
        point = TimeSeriesPoint(timestamp=DAY_1, value=1.0)
        assert dict(point.scope) == {}

    def test_scope_is_frozen_into_a_read_only_mapping(self) -> None:
        point = TimeSeriesPoint(timestamp=DAY_1, value=1.0, scope={"pit": "north"})
        with pytest.raises(TypeError):
            point.scope["pit"] = "south"  # type: ignore[index]


class TestTimeSeriesConstruction:
    def test_points_are_sorted_by_timestamp(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_2, value=2.0),
                TimeSeriesPoint(timestamp=DAY_1, value=1.0),
            )
        )
        assert [point.timestamp for point in series.points] == [DAY_1, DAY_2]

    def test_len(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_1, value=1.0),
                TimeSeriesPoint(timestamp=DAY_2, value=2.0),
            )
        )
        assert len(series) == 2

    def test_empty_series_has_length_zero(self) -> None:
        assert len(TimeSeries(points=())) == 0

    def test_values_returns_floats_in_timestamp_order(self) -> None:
        series = TimeSeries(
            points=(
                TimeSeriesPoint(timestamp=DAY_2, value=2.0),
                TimeSeriesPoint(timestamp=DAY_1, value=1.0),
            )
        )
        assert series.values() == (1.0, 2.0)


class TestFromKPIResults:
    def test_wraps_results_with_matching_timestamps(self) -> None:
        results = [
            KPIResult(code="PROD.TPH", value=100.0, unit="t/h"),
            KPIResult(code="PROD.TPH", value=200.0, unit="t/h"),
        ]
        series = TimeSeries.from_kpi_results(results, timestamps=[DAY_1, DAY_2])
        assert series.values() == (100.0, 200.0)

    def test_none_value_defaults_to_zero(self) -> None:
        results = [KPIResult(code="PROD.TPH", value=None, unit="t/h")]
        series = TimeSeries.from_kpi_results(results, timestamps=[DAY_1])
        assert series.values() == (0.0,)

    def test_scope_is_carried_from_the_kpi_result(self) -> None:
        results = [KPIResult(code="PROD.TPH", value=100.0, unit="t/h", scope={"pit": "north"})]
        series = TimeSeries.from_kpi_results(results, timestamps=[DAY_1])
        assert series.points[0].scope["pit"] == "north"

    def test_mismatched_lengths_raise(self) -> None:
        results = [KPIResult(code="PROD.TPH", value=100.0, unit="t/h")]
        with pytest.raises(AnalyticsValidationError, match="exactly one timestamp"):
            TimeSeries.from_kpi_results(results, timestamps=[DAY_1, DAY_2])


class TestFromEventQuery:
    def test_wraps_matching_envelopes(
        self,
        event_store: _InMemoryEventStore,
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        first = cycle_envelope_factory(event_time=DAY_1, payload=None)
        second = cycle_envelope_factory(event_time=DAY_2, payload=None)
        event_store.append(first)
        event_store.append(second)

        series = TimeSeries.from_event_query(event_store, EventQuery(), value_field="payload_t")

        assert len(series) == 2
        assert series.values() == (220.0, 220.0)

    def test_scope_is_populated_from_equipment_and_shift_id(
        self,
        event_store: _InMemoryEventStore,
        cycle_event_factory: Callable[..., CycleEvent],
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        payload = cycle_event_factory(equipment_id="HT-214", shift_id="A-2026-06-25")
        event_store.append(cycle_envelope_factory(payload=payload, event_time=DAY_1))

        series = TimeSeries.from_event_query(event_store, EventQuery(), value_field="payload_t")

        assert series.points[0].scope["equipment_id"] == "HT-214"
        assert series.points[0].scope["shift_id"] == "A-2026-06-25"

    def test_empty_store_yields_empty_series(self, event_store: _InMemoryEventStore) -> None:
        series = TimeSeries.from_event_query(event_store, EventQuery(), value_field="payload_t")
        assert len(series) == 0

    def test_payload_without_equipment_or_shift_id_yields_empty_scope(
        self,
        event_store: _InMemoryEventStore,
        cycle_envelope_factory: Callable[..., EventEnvelope[CycleEvent]],
    ) -> None:
        """``from_event_query`` accepts ``EventStore[Any]`` -- looser than the
        ``BaseEvent``-bound ``EventEnvelope[TEvent]`` every real producer in
        this platform uses -- so it must not crash on a payload that lacks
        ``equipment_id``/``shift_id`` entirely, only omit them from scope."""

        class _BarePayload:
            payload_t = 220.0

        envelope = cycle_envelope_factory(event_time=DAY_1, payload=None)
        bare_envelope = envelope.replace(payload=_BarePayload())
        event_store.append(bare_envelope)

        series = TimeSeries.from_event_query(event_store, EventQuery(), value_field="payload_t")

        assert len(series) == 1
        assert dict(series.points[0].scope) == {}
