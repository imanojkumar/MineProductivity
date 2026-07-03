"""Tests for mineproductivity.connectors.network.graphql_connector."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

import pytest

from mineproductivity.core import Result
from mineproductivity.connectors.auth import AuthProvider, Credentials, _StaticAuthProvider
from mineproductivity.connectors.exceptions import AuthenticationError, SourceUnavailableError
from mineproductivity.connectors.health import HealthStatus
from mineproductivity.connectors.network.graphql_connector import GraphQLConnector
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


class TestQuery:
    def test_yields_cycles_from_data_field(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                _json_response(self, 200, {"data": {"cycles": [_RECORD]}})

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1

    def test_delays_from_data_field(self, run_server) -> None:  # type: ignore[no-untyped-def]
        delay_record = {
            "event_time": "2026-06-25T06:00:00",
            "equipment_id": "CR-01",
            "delay_category": "EQUIPMENT",
            "delay_reason": "crusher_down",
            "duration_min": 252.0,
        }

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                _json_response(self, 200, {"data": {"delays": [delay_record]}})

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        delays = list(conn.get_delay_data(_SINCE, _UNTIL))
        assert len(delays) == 1

    def test_401_triggers_refresh_and_retry(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                auth = self.headers.get("Authorization", "")
                if "gen0" in auth:
                    self.send_response(401)
                    self.end_headers()
                    return
                _json_response(self, 200, {"data": {"cycles": [_RECORD]}})

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1
        health = conn.health_check()
        assert health.status is HealthStatus.HEALTHY
        assert health.last_successful_pull_utc is not None

    def test_malformed_record_skipped_others_ingest(self, run_server) -> None:  # type: ignore[no-untyped-def]
        bad_record = {**_RECORD, "payload_t": "NOT_A_NUMBER"}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                _json_response(self, 200, {"data": {"cycles": [bad_record, _RECORD]}})

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        events = list(conn.get_cycle_data(_SINCE, _UNTIL))
        assert len(events) == 1

    def test_refresh_failure_raises_authentication_error(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                self.send_response(401)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _NeverRefreshingAuthProvider()
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        with pytest.raises(AuthenticationError, match="credential refresh failed"):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_persistent_401_raises(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                self.send_response(401)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(endpoint, provider, RetryPolicy(base_delay_s=0.0), shift_id="A")
        with pytest.raises(AuthenticationError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_server_error_raises_source_unavailable(self, run_server) -> None:  # type: ignore[no-untyped-def]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                self.send_response(500)
                self.end_headers()

            def log_message(self, *args: object) -> None:
                pass

        endpoint = run_server(Handler)
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(
            endpoint, provider, RetryPolicy(max_attempts=1, base_delay_s=0.0), shift_id="A"
        )
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))

    def test_unreachable_endpoint_raises(self) -> None:
        provider = _StaticAuthProvider(base_token="tok")
        conn = GraphQLConnector(
            "http://127.0.0.1:1",
            provider,
            RetryPolicy(max_attempts=1, base_delay_s=0.0),
            shift_id="A",
        )
        with pytest.raises(SourceUnavailableError):
            list(conn.get_cycle_data(_SINCE, _UNTIL))


class TestConnectorMetadata:
    def test_name(self) -> None:
        assert GraphQLConnector.name == "graphql"
