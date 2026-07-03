"""Tests for mineproductivity.connectors.file.csv_connector."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from mineproductivity.connectors.exceptions import SourceUnavailableError
from mineproductivity.connectors.file.csv_connector import CSVConnector
from mineproductivity.connectors.health import HealthStatus

_SINCE = datetime(2026, 6, 25, 0, 0, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, 0, 0, tzinfo=timezone.utc)

_CYCLE_HEADER = (
    "event_time,equipment_id,queue_min,spot_min,load_min,haul_min,dump_min,return_min,payload_t\n"
)
_DELAY_HEADER = "event_time,equipment_id,delay_category,delay_reason,duration_min\n"


@pytest.fixture
def cycles_csv(tmp_path: Path) -> Path:
    path = tmp_path / "cycles.csv"
    path.write_text(
        _CYCLE_HEADER
        + "2026-06-25T06:00:00,HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n"
        + "2026-06-25T07:00:00,HT-215,1.2,0.4,2.6,8.1,1.1,5.9,218.0\n"
        + "2026-06-27T07:00:00,HT-216,1.2,0.4,2.6,8.1,1.1,5.9,218.0\n",
        encoding="utf-8",
    )
    return path


class TestGetCycleData:
    def test_returns_a_generator_not_a_list(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        result = conn.get_cycle_data(_SINCE, _UNTIL)
        assert not isinstance(result, list)
        assert hasattr(result, "__iter__")

    def test_respects_since_until_window(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 2
        assert {e.equipment_id for e in events} == {"HT-214", "HT-215"}

    def test_injects_constructor_shift_id(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="SHIFT-XYZ")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert all(e.shift_id == "SHIFT-XYZ" for e in events)

    def test_narrow_window_excludes_out_of_range_rows(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        narrow_until = datetime(2026, 6, 25, 6, 30, tzinfo=timezone.utc)
        events = list(conn.get_cycle_data(_SINCE, narrow_until))
        assert len(events) == 1
        assert events[0].equipment_id == "HT-214"

    def test_missing_file_raises_source_unavailable(self, tmp_path: Path) -> None:
        conn = CSVConnector(tmp_path / "does-not-exist.csv", shift_id="A")
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_os_error_mid_read_raises_source_unavailable(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        with patch.object(Path, "open", side_effect=OSError("permission denied")):
            with pytest.raises(SourceUnavailableError, match="failed to read"):
                list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNHEALTHY

    def test_empty_header_only_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.csv"
        path.write_text(_CYCLE_HEADER, encoding="utf-8")
        conn = CSVConnector(path, shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_malformed_row_skipped_others_ingest(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.csv"
        path.write_text(
            _CYCLE_HEADER
            + "2026-06-25T06:00:00,HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n"
            + "2026-06-25T07:00:00,HT-215,BAD,0.4,2.6,8.1,1.1,5.9,218.0\n"
            + "2026-06-25T08:00:00,HT-216,1.2,0.4,2.6,8.1,1.1,5.9,218.0\n",
            encoding="utf-8",
        )
        conn = CSVConnector(path, shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 2
        assert {e.equipment_id for e in events} == {"HT-214", "HT-216"}

    def test_row_missing_event_time_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.csv"
        path.write_text(
            _CYCLE_HEADER + ",HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n",
            encoding="utf-8",
        )
        conn = CSVConnector(path, shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_row_with_unparseable_event_time_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.csv"
        path.write_text(
            _CYCLE_HEADER + "not-a-date,HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n",
            encoding="utf-8",
        )
        conn = CSVConnector(path, shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_local_timezone_normalization(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.csv"
        path.write_text(
            _CYCLE_HEADER + "2026-06-24T23:00:00,HT-214,1.5,0.5,2.5,8.0,1.0,6.0,220.0\n",
            encoding="utf-8",
        )
        conn = CSVConnector(path, shift_id="A", source_timezone="Australia/Perth")
        narrow_since = datetime(2026, 6, 24, 14, 30, tzinfo=timezone.utc)
        narrow_until = datetime(2026, 6, 24, 15, 30, tzinfo=timezone.utc)
        events = list(conn.get_cycle_data(narrow_since, narrow_until))
        assert len(events) == 1


class TestGetDelayData:
    def test_no_delay_path_yields_nothing(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        assert list(conn.get_delay_data(_SINCE, _UNTIL)) == []

    def test_reads_the_separate_delay_file(self, tmp_path: Path, cycles_csv: Path) -> None:
        delay_path = tmp_path / "delays.csv"
        delay_path.write_text(
            _DELAY_HEADER + "2026-06-25T06:00:00,CR-01,EQUIPMENT,crusher_down,252.0\n",
            encoding="utf-8",
        )
        conn = CSVConnector(cycles_csv, shift_id="A", delay_path=delay_path)
        delays = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(delays) == 1
        assert delays[0].delay_category.name == "EQUIPMENT"

    def test_missing_delay_file_raises(self, cycles_csv: Path, tmp_path: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A", delay_path=tmp_path / "missing-delays.csv")
        with pytest.raises(SourceUnavailableError):
            list(conn.get_delay_data(_SINCE, _UNTIL))


class TestHealthCheck:
    def test_unknown_before_any_pull(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        assert conn.health_check().status is HealthStatus.UNKNOWN

    def test_healthy_after_successful_pull(self, cycles_csv: Path) -> None:
        conn = CSVConnector(cycles_csv, shift_id="A")
        list(conn.get_cycle_data(_SINCE, _UNTIL))
        health = conn.health_check()
        assert health.status is HealthStatus.HEALTHY
        assert health.last_successful_pull_utc is not None

    def test_unhealthy_after_missing_file(self, tmp_path: Path) -> None:
        conn = CSVConnector(tmp_path / "missing.csv", shift_id="A")
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNHEALTHY


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert CSVConnector.name == "csv"

    def test_provided_event_types(self) -> None:
        assert CSVConnector.provided_event_types() == ("cycle", "delay")
