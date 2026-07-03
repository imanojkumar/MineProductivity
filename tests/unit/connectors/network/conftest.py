"""Shared fixtures for network connector tests: a real, local HTTP server
(no mocking library) so RestConnector/GraphQLConnector are tested
against genuine socket I/O, matching the checklist's "mocked HTTP
server demonstrating auth-refresh and retry/backoff" requirement with a
lightweight stdlib server rather than a patched client.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

ServerFactory = Callable[[type[BaseHTTPRequestHandler]], str]


class _SilentHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass


@pytest.fixture
def run_server() -> Iterator[ServerFactory]:
    """Yield a factory: ``run_server(handler_cls) -> base_url``. The
    server is torn down automatically at the end of the test."""
    servers: list[HTTPServer] = []
    threads: list[threading.Thread] = []

    def start(handler_cls: type[BaseHTTPRequestHandler]) -> str:
        server = HTTPServer(("127.0.0.1", 0), handler_cls)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        servers.append(server)
        threads.append(thread)
        return f"http://127.0.0.1:{server.server_port}"

    yield start

    for server in servers:
        server.shutdown()
    for thread in threads:
        thread.join(timeout=5)


@pytest.fixture
def silent_handler() -> type[BaseHTTPRequestHandler]:
    return _SilentHandler
