"""Integration test for the Connector Framework: the full pipeline from a
real CSV fixture, through the reference ``CSVConnector``, into the Event
Framework's contextual validation, durable append, and query -- no
direct function call bypassing a stage (design spec §30, mirroring
Event Framework spec §30 Category B "since it is the same pipeline
observed from the connector side").
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from mineproductivity.events import EventEnvelope, EventID, EventQuery, EventValidator, EventVersion
from mineproductivity.events.store import _InMemoryEventStore

from mineproductivity.connectors import CSVConnector

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "connectors"

_SINCE = datetime(2026, 6, 25, 0, 0, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, 0, 0, tzinfo=timezone.utc)


class TestGoldenReproduction:
    """Category A: the golden fixtures, run through CSVConnector,
    reproduce the golden CycleEvent/DelayEvent instances exactly."""

    def test_cycle_events_reproduced_exactly(self) -> None:
        connector = CSVConnector(_FIXTURES_DIR / "cycle_events.csv", shift_id="A-2026-06-25")
        events = list(connector.get_cycle_data(_SINCE, _UNTIL))

        assert len(events) == 4
        first = events[0]
        assert first.equipment_id == "HT-214"
        assert first.shift_id == "A-2026-06-25"
        assert first.payload_t == 220.0
        assert first.route_id == "RT-1"
        assert first.operator_id == "OP-101"
        assert first.material_type == "ore"
        assert round(first.cycle_min, 2) == 19.5

    def test_delay_events_reproduced_exactly(self) -> None:
        connector = CSVConnector(
            _FIXTURES_DIR / "cycle_events.csv",
            shift_id="A-2026-06-25",
            delay_path=_FIXTURES_DIR / "delay_events.csv",
        )
        delays = list(connector.get_delay_data(_SINCE, _UNTIL))

        assert len(delays) == 3
        first = delays[0]
        assert first.equipment_id == "CR-01"
        assert first.delay_category.name == "EQUIPMENT"
        assert first.delay_reason == "crusher_down"
        assert first.duration_min == 252.0


class TestFullPipelineNoStageBypassed:
    """Category B: CSV -> CSVConnector -> EventValidator -> EventStore ->
    query reproduces golden outputs, exactly mirroring the Event
    Framework's own integration test but sourced through a real
    connector instead of an inline parsing helper."""

    def test_end_to_end_ingestion_and_query(self) -> None:
        connector = CSVConnector(_FIXTURES_DIR / "cycle_events.csv", shift_id="A-2026-06-25")
        validator = EventValidator()
        store = _InMemoryEventStore()

        cycles = list(connector.get_cycle_data(_SINCE, _UNTIL))
        assert len(cycles) == 4, "connector produced canonical events, not raw CSV rows"

        for i, cycle in enumerate(cycles):
            outcome = validator.validate_with_confidence(cycle)
            assert outcome.is_valid

            event_time = _SINCE.replace(hour=6, minute=i * 15)
            envelope = EventEnvelope(
                event_id=EventID.generate(),
                version=EventVersion(),
                payload=cycle,
                event_time_utc=event_time,
                processing_time_utc=event_time,
                ingestion_time_utc=event_time,
            )
            result = store.append(envelope)
            assert result.is_ok

        ht214_events = list(store.query(EventQuery(equipment_ids=("HT-214",))))
        assert len(ht214_events) == 2
        assert {e.payload.payload_t for e in ht214_events} == {220.0, 221.0}


class TestEdgeCases:
    """Category C: an empty CSV (zero rows), a [since, until) window with
    no matching records, and a record with every optional field absent
    are all handled without error."""

    def test_empty_csv_zero_rows(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        path.write_text(
            "event_time,equipment_id,queue_min,spot_min,load_min,haul_min,dump_min,return_min,payload_t\n",
            encoding="utf-8",
        )
        connector = CSVConnector(path, shift_id="A")
        assert list(connector.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_window_with_no_matching_records(self) -> None:
        connector = CSVConnector(_FIXTURES_DIR / "cycle_events.csv", shift_id="A-2026-06-25")
        far_future_since = datetime(2030, 1, 1, tzinfo=timezone.utc)
        far_future_until = datetime(2030, 1, 2, tzinfo=timezone.utc)
        assert list(connector.get_cycle_data(far_future_since, far_future_until)) == []

    def test_record_with_every_optional_field_absent(self, tmp_path: Path) -> None:
        path = tmp_path / "minimal.csv"
        path.write_text(
            "event_time,equipment_id,queue_min,spot_min,load_min,haul_min,dump_min,return_min,payload_t\n"
            "2026-06-25T06:00:00,HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n",
            encoding="utf-8",
        )
        connector = CSVConnector(path, shift_id="A")
        events = list(connector.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        assert events[0].route_id is None
        assert events[0].operator_id is None
        assert events[0].material_type == "unspecified"


class TestCorruptedData:
    """Category D: a malformed CSV row (non-numeric payload, missing
    required column) produces a skipped row, never a crash -- the rest
    of the file still ingests."""

    def test_malformed_rows_isolated_rest_ingest(self) -> None:
        connector = CSVConnector(
            _FIXTURES_DIR / "malformed_cycle_events.csv", shift_id="A-2026-06-25"
        )
        events = list(connector.get_cycle_data(_SINCE, _UNTIL))
        # 9 total data rows, 2 malformed (non-numeric queue_min; blank payload_t).
        assert len(events) == 7
        assert "HT-215" not in {e.equipment_id for e in events}  # non-numeric queue_min
        assert "HT-218" not in {e.equipment_id for e in events}  # blank payload_t


class TestTimezoneNormalization:
    """Category F: a CSV with local (non-UTC) timestamps is correctly
    normalized to event_time_utc, applied at the connector boundary
    since that is where raw timestamps first enter the platform."""

    def test_local_timestamps_normalized_to_utc(self) -> None:
        connector = CSVConnector(
            _FIXTURES_DIR / "local_timezone_cycle_events.csv",
            shift_id="A-2026-06-25",
            source_timezone="Australia/Perth",
        )
        # Perth is UTC+8: 2026-06-24T22:00 local == 2026-06-24T14:00 UTC,
        # and 2026-06-24T23:30 local == 2026-06-24T15:30 UTC.
        narrow_since = datetime(2026, 6, 24, 13, 0, tzinfo=timezone.utc)
        narrow_until = datetime(2026, 6, 24, 16, 0, tzinfo=timezone.utc)
        events = list(connector.get_cycle_data(narrow_since, narrow_until))
        assert len(events) == 2
