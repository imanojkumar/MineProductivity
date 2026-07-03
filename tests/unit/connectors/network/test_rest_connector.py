"""Tests for mineproductivity.connectors.network.rest_connector.

Exercises RestConnector against a real, local ``http.server.HTTPServer``
-- genuine socket I/O, not a patched client -- per the checklist's
"mocked HTTP server demonstrating auth-refresh and retry/backoff"
requirement.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import pytest

from mineproductivity.core import Result
from mineproductivity.connectors.auth import AuthProvider, Credentials, _StaticAuthProvider
from mineproductivity.connectors.exceptions import AuthenticationError, SourceUnavailableError
from mineproductivity.connectors.health import HealthStatus
from mineproductivity.connectors.network.rest_connector import RestConnector
from mineproductivity.connectors.retry import RetryPolicy

_SINCE = datetime(2026, 6, 25, tzinfo=timezone.utc)
_UNTIL = datetime(2026, 6, 26, tzinfo=timezone.utc)

_RECORD = {
    "event_time": "2026-06-25T06:00:00",
    "equipment_id": "HT-214",
    "queue_min": 1.0,
    "spot_min": 0.5,
    "load_min": 2.0,
    "haul_min": 8.0,
    "dump_min": 1.0,
    "return_min": 6.0,
    "payload_t": 220.0,
}


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict) -> None:  # type: ignore[type-arg]
    payload = json.dumps(body).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(payload)


class _NeverRefreshingAuthProvider(AuthProvider):
    def credentials(self) -> Credentials:
        return Credentials(token="stale-token")

    def refresh(self) -> Result[Credentials]:
        return Result.err("refresh always fails for this fixture provider")


class TestSinglePageSuccess:
    def test_yields_one_event_from_one_page(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                _json_response(self, 200, {"records": [_RECORD], "has_more": False})

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        assert events[0].equipment_id == "HT-214"
        assert conn.health_check().status is HealthStatus.HEALTHY


class TestPagination:
    def test_follows_has_more_across_pages(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                if "page=0" in self.path:
                    _json_response(self, 200, {"records": [_RECORD], "has_more": True})
                elif "page=1" in self.path:
                    _json_response(self, 200, {"records": [_RECORD], "has_more": False})
                else:
                    _json_response(self, 200, {"records": [], "has_more": False})

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 2


class TestAuthRefresh:
    def test_401_triggers_refresh_and_retry(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                auth = self.headers.get("Authorization", "")
                if "gen0" in auth:
                    self.send_response(401)
                    self.end_headers()
                    return
                _json_response(self, 200, {"records": [_RECORD], "has_more": False})

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1

    def test_persistent_401_raises_authentication_error(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(401)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        with pytest.raises(AuthenticationError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert conn.health_check().status is HealthStatus.UNHEALTHY

    def test_refresh_failure_raises_authentication_error(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(401)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _NeverRefreshingAuthProvider()
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        with pytest.raises(AuthenticationError, match="credential refresh failed"):
            list(conn.get_cycle_data(_SINCE, _UNTIL))


class TestServerErrors:
    def test_500_is_retried_then_raises_source_unavailable(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                self.send_response(500)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(
            base_url, provider, RetryPolicy(max_attempts=2, base_delay_s=0.0), shift_id="A"
        )
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_unreachable_host_raises_source_unavailable(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(
            "http://127.0.0.1:1",
            provider,
            RetryPolicy(max_attempts=1, base_delay_s=0.0),
            shift_id="A",
        )
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))


class TestMalformedRecordIsolation:
    def test_one_bad_record_skipped_others_ingest(self, run_server) -> None:  # type: ignore[no-untyped-def]
        bad_record = {**_RECORD, "payload_t": "NOT_A_NUMBER"}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                _json_response(self, 200, {"records": [bad_record, _RECORD], "has_more": False})

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1


class TestGetDelayData:
    def test_delay_records_translated(self, run_server) -> None:  # type: ignore[no-untyped-def]
        delay_record = {
            "event_time": "2026-06-25T06:00:00",
            "equipment_id": "CR-01",
            "delay_category": "EQUIPMENT",
            "delay_reason": "crusher_down",
            "duration_min": 252.0,
        }

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                _json_response(self, 200, {"records": [delay_record], "has_more": False})

            def log_message(self, *args: object) -> None:
                pass

        base_url = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = RestConnector(base_url, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        delays = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(delays) == 1


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert RestConnector.name == "rest"
