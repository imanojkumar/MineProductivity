"""RestConnector against a real, local HTTP server, demonstrating
pagination, a 401-triggered auth refresh, and retry/backoff on a
transient server error.

Run: python examples/connectors/02_rest_with_retry.py
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from mineproductivity.connectors import BackoffStrategy, RestConnector, RetryPolicy
from mineproductivity.connectors.auth import _StaticAuthProvider

_RECORD = {
    "event_time": "2026-06-25T06:00:00",
    "equipment_id": "HT-214",
    "queue_min": 1.5,
    "spot_min": 0.5,
    "load_min": 2.5,
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


class DemoHandler(BaseHTTPRequestHandler):
    """Serves page 0 only after a valid (refreshed) token is presented,
    and fails the first attempt at page 1 to demonstrate retry/backoff."""

    request_count = 0

    def do_GET(self) -> None:  # noqa: N802
        auth = self.headers.get("Authorization", "")
        if "gen0" in auth:
            self.send_response(401)  # stale token -- forces a refresh
            self.end_headers()
            return
        if "page=0" in self.path:
            _json_response(self, 200, {"records": [_RECORD], "has_more": True})
            return
        DemoHandler.request_count += 1
        if DemoHandler.request_count == 1:
            self.send_response(503)  # transient failure -- forces a retry
            self.end_headers()
            return
        _json_response(self, 200, {"records": [_RECORD], "has_more": False})

    def log_message(self, *args: object) -> None:
        pass  # silence the demo's console noise


def main() -> None:
    server = HTTPServer(("127.0.0.1", 0), DemoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        print(f"--- Demo server running at {base_url} ---")

        print()
        print("--- 1. AuthProvider + RetryPolicy configuration ---")
        auth = _StaticAuthProvider(base_token="tok")
        retry = RetryPolicy(max_attempts=3, backoff=BackoffStrategy.EXPONENTIAL, base_delay_s=0.1)
        connector = RestConnector(base_url, auth, retry, shift_id="A-2026-06-25")

        print()
        print(
            "--- 2. First request gets a 401 (stale token); AuthProvider.refresh() is called once ---"
        )
        print(
            "--- 3. Page 1's first attempt gets a transient 503; RetryPolicy retries automatically ---"
        )
        since = datetime(2026, 6, 25, tzinfo=timezone.utc)
        until = datetime(2026, 6, 26, tzinfo=timezone.utc)
        events = list(connector.get_cycle_data(since, until))

        print()
        print(
            f"--- 4. Result: {len(events)} events ingested despite the 401 and the transient 503 ---"
        )
        print(f"health_check(): {connector.health_check().status}")
    finally:
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
