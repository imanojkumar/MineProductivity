"""Tests for mineproductivity.digital_twin.telemetry."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import mineproductivity.digital_twin.telemetry as telemetry_module
from mineproductivity.core import BaseValueObject
from mineproductivity.core.serialization import DataclassSerializer, to_dict
from mineproductivity.digital_twin.telemetry import TelemetryReading

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _reading() -> TelemetryReading:
    return TelemetryReading(
        sensor_id="CONV-7.belt_speed", value=3.1, unit="m/s", observed_at=_EPOCH
    )


class TestTelemetryReading:
    def test_carries_one_observed_reading(self) -> None:
        reading = _reading()
        assert reading.sensor_id == "CONV-7.belt_speed"
        assert reading.value == 3.1
        assert reading.unit == "m/s"
        assert reading.observed_at is _EPOCH

    def test_is_a_plain_value_object(self) -> None:
        assert issubclass(TelemetryReading, BaseValueObject)

    def test_value_equality(self) -> None:
        assert _reading() == _reading()

    def test_round_trips_via_dataclass_serializer(self) -> None:
        serializer = DataclassSerializer(TelemetryReading)
        assert serializer.deserialize(serializer.serialize(_reading())) == _reading()

    def test_to_dict_works_generically(self) -> None:
        assert to_dict(_reading())["unit"] == "m/s"


class TestNotASecondIngestionBoundary:
    """Design spec §16, checklist Package Structure: ``telemetry.py``
    contains no direct import of, or reference to, any
    ``connectors``-package class -- telemetry integration composes over
    already-event-sourced data only."""

    def test_telemetry_module_never_imports_connectors(self) -> None:
        source = Path(telemetry_module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("mineproductivity.connectors")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("mineproductivity.connectors")
