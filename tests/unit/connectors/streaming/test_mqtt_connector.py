"""Tests for mineproductivity.connectors.streaming.mqtt_connector."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.connectors.health import HealthStatus
from mineproductivity.connectors.streaming.mqtt_connector import MqttConnector

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
        conn = MqttConnector("mine/+/cycles", shift_id="A")
        assert list(conn.get_cycle_data(_SINCE, _UNTIL)) == []

    def test_consumes_injected_source(self) -> None:
        conn = MqttConnector("mine/+/cycles", shift_id="A", cycle_source=[_MESSAGE])
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1


class TestGetDelayData:
    def test_no_source_yields_nothing(self) -> None:
        conn = MqttConnector("mine/+/delays", shift_id="A")
        assert list(conn.get_delay_data(_SINCE, _UNTIL)) == []

    def test_consumes_injected_source(self) -> None:
        conn = MqttConnector("mine/+/delays", shift_id="A", delay_source=[_DELAY_MESSAGE])
        events = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(events) == 1


class TestHealthCheck:
    def test_healthy_after_first_message(self) -> None:
        conn = MqttConnector("mine/+/cycles", shift_id="A", cycle_source=[_MESSAGE])
        list(conn.get_cycle_data(_SINCE, _UNTIL))
        health = conn.health_check()
        assert health.status is HealthStatus.HEALTHY
        assert "mine/+/cycles" in health.detail


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert MqttConnector.name == "mqtt"
