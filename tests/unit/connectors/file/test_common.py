"""Tests for mineproductivity.connectors.file._common."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mineproductivity.connectors.exceptions import MappingError
from mineproductivity.connectors.file._common import FileRowNormalizer, parse_source_datetime
from mineproductivity.connectors.normalization import FieldMapper


def _cycle_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = dict(
        equipment_id="HT-214",
        shift_id="A-2026-06-25",
        queue_min="1.5",
        spot_min="0.5",
        load_min="2.5",
        haul_min="8.0",
        dump_min="1.0",
        return_min="6.0",
        payload_t="220.0",
    )
    row.update(overrides)
    return row


def _delay_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = dict(
        equipment_id="CR-01",
        shift_id="A-2026-06-25",
        delay_category="EQUIPMENT",
        delay_reason="crusher_down",
        duration_min="252.0",
    )
    row.update(overrides)
    return row


class TestFileRowNormalizerCycle:
    def test_valid_row(self) -> None:
        normalizer = FileRowNormalizer()
        event = normalizer.normalize_cycle(_cycle_row())
        assert event.equipment_id == "HT-214"
        assert event.payload_t == 220.0

    def test_optional_fields_default(self) -> None:
        normalizer = FileRowNormalizer()
        event = normalizer.normalize_cycle(_cycle_row())
        assert event.route_id is None
        assert event.operator_id is None
        assert event.material_type == "unspecified"

    def test_optional_fields_populated(self) -> None:
        normalizer = FileRowNormalizer()
        event = normalizer.normalize_cycle(
            _cycle_row(route_id="RT-1", operator_id="OP-1", material_type="ore")
        )
        assert event.route_id == "RT-1"
        assert event.operator_id == "OP-1"
        assert event.material_type == "ore"

    def test_missing_required_field_raises_mapping_error(self) -> None:
        row = _cycle_row()
        del row["payload_t"]
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="missing required field"):
            normalizer.normalize_cycle(row)

    def test_non_numeric_field_raises_mapping_error(self) -> None:
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="non-numeric"):
            normalizer.normalize_cycle(_cycle_row(payload_t="not-a-number"))

    def test_event_validation_failure_raises_mapping_error(self) -> None:
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="validation"):
            normalizer.normalize_cycle(_cycle_row(payload_t="-5.0"))

    def test_field_mapper_applied_before_normalization(self) -> None:
        mapper = FieldMapper(mapping={"TruckID": "equipment_id"})
        normalizer = FileRowNormalizer(field_mapper=mapper)
        row = _cycle_row()
        del row["equipment_id"]
        row["TruckID"] = "HT-999"
        event = normalizer.normalize_cycle(row)
        assert event.equipment_id == "HT-999"


class TestFileRowNormalizerDelay:
    def test_valid_row(self) -> None:
        normalizer = FileRowNormalizer()
        event = normalizer.normalize_delay(_delay_row())
        assert event.delay_category.name == "EQUIPMENT"
        assert event.duration_min == 252.0

    def test_missing_required_field_raises_mapping_error(self) -> None:
        row = _delay_row()
        del row["duration_min"]
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="missing required field"):
            normalizer.normalize_delay(row)

    def test_non_numeric_duration_raises_mapping_error(self) -> None:
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="non-numeric"):
            normalizer.normalize_delay(_delay_row(duration_min="oops"))

    def test_unrecognized_delay_category_raises_mapping_error(self) -> None:
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="unrecognized delay_category"):
            normalizer.normalize_delay(_delay_row(delay_category="NOT_A_CATEGORY"))

    def test_delay_category_case_insensitive(self) -> None:
        normalizer = FileRowNormalizer()
        event = normalizer.normalize_delay(_delay_row(delay_category="equipment"))
        assert event.delay_category.name == "EQUIPMENT"

    def test_event_validation_failure_raises_mapping_error(self) -> None:
        normalizer = FileRowNormalizer()
        with pytest.raises(MappingError, match="validation"):
            normalizer.normalize_delay(_delay_row(delay_reason=""))


class TestParseSourceDatetime:
    def test_naive_string_localized_to_source_timezone(self) -> None:
        result = parse_source_datetime("2026-06-25T06:00:00", source_timezone="UTC")
        assert result == datetime(2026, 6, 25, 6, tzinfo=timezone.utc)

    def test_non_utc_local_time_converted_to_utc(self) -> None:
        # 2026-06-24T23:00:00 in Australia/Perth (UTC+8) == 15:00 UTC.
        result = parse_source_datetime("2026-06-24T23:00:00", source_timezone="Australia/Perth")
        assert result == datetime(2026, 6, 24, 15, tzinfo=timezone.utc)

    def test_already_aware_string_converted_to_utc(self) -> None:
        result = parse_source_datetime("2026-06-25T06:00:00+08:00", source_timezone="UTC")
        assert result == datetime(2026, 6, 24, 22, tzinfo=timezone.utc)

    def test_unparseable_string_raises_mapping_error(self) -> None:
        with pytest.raises(MappingError, match="unparseable"):
            parse_source_datetime("not-a-date", source_timezone="UTC")
