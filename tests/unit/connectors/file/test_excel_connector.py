"""Tests for mineproductivity.connectors.file.excel_connector."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import openpyxl
import pytest

from mineproductivity.connectors.exceptions import SourceUnavailableError
from mineproductivity.connectors.file.excel_connector import ExcelConnector
from mineproductivity.connectors.health import HealthStatus

_SINCE = datetime(2026, 6, 25, 0, 0, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, 0, 0, tzinfo=timezone.utc)

_CYCLE_HEADER = [
    "event_time",
    "equipment_id",
    "queue_min",
    "spot_min",
    "load_min",
    "haul_min",
    "dump_min",
    "return_min",
    "payload_t",
]
_DELAY_HEADER = ["event_time", "equipment_id", "delay_category", "delay_reason", "duration_min"]


def _write_workbook(path: Path, header: list[str], rows: list[list[object]]) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(header)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


@pytest.fixture
def cycles_xlsx(tmp_path: Path) -> Path:
    path = tmp_path / "cycles.xlsx"
    _write_workbook(
        path,
        _CYCLE_HEADER,
        [
            ["2026-06-25T06:00:00", "HT-214", 1.5, 0.5, 2.5, 8.0, 1.0, 6.0, 220.0],
            ["2026-06-27T07:00:00", "HT-216", 1.2, 0.4, 2.6, 8.1, 1.1, 5.9, 218.0],
        ],
    )
    return path


class TestGetCycleData:
    def test_returns_a_generator_not_a_list(self, cycles_xlsx: Path) -> None:
        conn = ExcelConnector(cycles_xlsx, shift_id="A")
        result = conn.get_cycle_data(_SINCE, _UNTIL)
        assert not isinstance(result, list)

    def test_respects_since_until_window(self, cycles_xlsx: Path) -> None:
        conn = ExcelConnector(cycles_xlsx, shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        assert events[0].equipment_id == "HT-214"

    def test_missing_file_raises_source_unavailable(self, tmp_path: Path) -> None:
        conn = ExcelConnector(tmp_path / "missing.xlsx", shift_id="A")
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_row_missing_event_time_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.xlsx"
        _write_workbook(
            path, _CYCLE_HEADER, [[None, "HT-214", 1.5, 0.5, 2.5, 8.0, 1.0, 6.0, 220.0]]
        )
        conn = ExcelConnector(path, shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_malformed_row_skipped_others_ingest(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.xlsx"
        _write_workbook(
            path,
            _CYCLE_HEADER,
            [
                ["2026-06-25T06:00:00", "HT-214", "BAD", 0.5, 2.5, 8.0, 1.0, 6.0, 220.0],
                ["2026-06-25T07:00:00", "HT-215", 1.2, 0.4, 2.6, 8.1, 1.1, 5.9, 218.0],
            ],
        )
        conn = ExcelConnector(path, shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        assert events[0].equipment_id == "HT-215"

    def test_row_with_unparseable_event_time_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "cycles.xlsx"
        _write_workbook(
            path, _CYCLE_HEADER, [["not-a-date", "HT-214", 1.5, 0.5, 2.5, 8.0, 1.0, 6.0, 220.0]]
        )
        conn = ExcelConnector(path, shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_os_error_mid_read_raises_source_unavailable(self, cycles_xlsx: Path) -> None:
        conn = ExcelConnector(cycles_xlsx, shift_id="A")
        with patch.object(ExcelConnector, "_iter_rows", side_effect=OSError("permission denied")):
            with pytest.raises(SourceUnavailableError, match="failed to read"):
                list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNHEALTHY


class TestGetDelayData:
    def test_no_delay_path_yields_nothing(self, cycles_xlsx: Path) -> None:
        conn = ExcelConnector(cycles_xlsx, shift_id="A")
        assert list(conn.get_delay_data(_SINCE, _UNTIL)) == []

    def test_reads_the_separate_delay_workbook(self, tmp_path: Path, cycles_xlsx: Path) -> None:
        delay_path = tmp_path / "delays.xlsx"
        _write_workbook(
            delay_path,
            _DELAY_HEADER,
            [["2026-06-25T06:00:00", "CR-01", "EQUIPMENT", "crusher_down", 252.0]],
        )
        conn = ExcelConnector(cycles_xlsx, shift_id="A", delay_path=delay_path)
        delays = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(delays) == 1


class TestHealthCheck:
    def test_healthy_after_successful_pull(self, cycles_xlsx: Path) -> None:
        conn = ExcelConnector(cycles_xlsx, shift_id="A")
        list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.HEALTHY

    def test_unhealthy_after_missing_file(self, tmp_path: Path) -> None:
        conn = ExcelConnector(tmp_path / "missing.xlsx", shift_id="A")
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNHEALTHY


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert ExcelConnector.name == "excel"
