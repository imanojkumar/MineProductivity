"""Tests for mineproductivity.connectors.health."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.connectors.health import ConnectorHealth, HealthStatus


class TestHealthStatus:
    def test_has_four_states(self) -> None:
        assert len(list(HealthStatus)) == 4

    def test_values(self) -> None:
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestConnectorHealth:
    def test_minimal_construction(self) -> None:
        health = ConnectorHealth(status=HealthStatus.UNKNOWN)
        assert health.status is HealthStatus.UNKNOWN
        assert health.last_successful_pull_utc is None
        assert health.detail == ""

    def test_full_construction(self) -> None:
        now = datetime(2026, 6, 25, 6, tzinfo=timezone.utc)
        health = ConnectorHealth(
            status=HealthStatus.HEALTHY, last_successful_pull_utc=now, detail="ok"
        )
        assert health.last_successful_pull_utc == now
        assert health.detail == "ok"

    def test_structural_equality(self) -> None:
        a = ConnectorHealth(status=HealthStatus.HEALTHY)
        b = ConnectorHealth(status=HealthStatus.HEALTHY)
        assert a == b
