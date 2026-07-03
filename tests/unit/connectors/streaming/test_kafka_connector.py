"""Tests for mineproductivity.connectors.streaming.kafka_connector."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.connectors.health import HealthStatus
from mineproductivity.connectors.streaming.kafka_connector import KafkaConnector

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)

_MESSAGE = {
    "equipment_id": "HT-214",
    "queue_min": 1.0,
    "spot_min": 0.5,
    "load_min": 2.0,
    "haul_min": 8.0,
    "dump_min": 1.0,
    "return_min": 6.0,
    "payload_t": 220.0,
}
_DELAY_MESSAGE = {
    "equipment_id": "CR-01",
    "delay_category": "EQUIPMENT",
    "delay_reason": "crusher_down",
    "duration_min": 252.0,
}


class TestGetCycleData:
    def test_no_source_yields_nothing(self) -> None:
        conn = KafkaConnector("cycles-topic", shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_consumes_injected_source(self) -> None:
        conn = KafkaConnector("cycles-topic", shift_id="A", cycle_source=[_MESSAGE])
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        assert events[0].equipment_id == "HT-214"

    def test_returns_a_lazy_generator(self) -> None:
        conn = KafkaConnector("cycles-topic", shift_id="A", cycle_source=[_MESSAGE])
        result = conn.get_cycle_data(_SINCE, _UNTIL)
        assert not isinstance(result, list)


class TestGetDelayData:
    def test_no_source_yields_nothing(self) -> None:
        conn = KafkaConnector("delays-topic", shift_id="A")
        assert list(conn.get_delay_data(_SINCE, _UNTIL)) == []

    def test_consumes_injected_source(self) -> None:
        conn = KafkaConnector("delays-topic", shift_id="A", delay_source=[_DELAY_MESSAGE])
        events = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(events) == 1


class TestHealthCheck:
    def test_unknown_before_any_message(self) -> None:
        conn = KafkaConnector("cycles-topic", shift_id="A", cycle_source=[])
        list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNKNOWN

    def test_healthy_after_first_message(self) -> None:
        conn = KafkaConnector("cycles-topic", shift_id="A", cycle_source=[_MESSAGE])
        list(conn.get_cycle_data(_SINCE, _UNTIL))
        health = conn.health_check()
        assert health.status is HealthStatus.HEALTHY
        assert health.last_successful_pull_utc is not None
        assert "cycles-topic" in health.detail


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert KafkaConnector.name == "kafka"

    def test_supported_modes_is_streaming(self) -> None:
        from mineproductivity.connectors.base import IngestionMode

        assert KafkaConnector.supported_modes == (IngestionMode.STREAMING,)
