"""``GraphQLConnector``: queries a GraphQL endpoint over HTTP POST,
yielding one event per record returned.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from typing import Any, ClassVar, TypeVar

from mineproductivity.connectors.auth import AuthProvider
from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.exceptions import (
    AuthenticationError,
    MappingError,
    SourceUnavailableError,
)
from mineproductivity.connectors.file._common import FileRowNormalizer
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus
from mineproductivity.connectors.normalization import Normalizer
from mineproductivity.connectors.retry import RetryPolicy, run_with_retry
from mineproductivity.events import CycleEvent, DelayEvent

__all__ = ["GraphQLConnector"]

_logger = logging.getLogger(__name__)
_TEvent = TypeVar("_TEvent")

_CYCLE_QUERY = "query($since: String!, $until: String!) { cycles(since: $since, until: $until) { equipmentId } }"
_DELAY_QUERY = "query($since: String!, $until: String!) { delays(since: $since, until: $until) { equipmentId } }"


class GraphQLConnector(FMSConnector):
    """Queries a GraphQL endpoint over HTTP POST (stdlib :mod:`urllib`
    only), yielding one event per record returned under the queried
    root field (``cycles``/``delays``).

    A reference-shape implementation: one request per pull (no cursor-
    based pagination), matching the design specification's brief
    ``__init__``-only sketch for this connector (§10.6, "follow the
    identical shape"). Real GraphQL sources with cursor pagination are
    expected to override :meth:`_query` in a subclass or plugin.

    Not thread-safe for concurrent calls against the same instance
    (design spec §24).
    """

    name: ClassVar[str] = "graphql"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (IngestionMode.BATCH,)

    def __init__(
        self,
        endpoint: str,
        auth: AuthProvider,
        retry: RetryPolicy,
        shift_id: str,
        *,
        normalizer: Normalizer | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        self._endpoint = endpoint
        self._auth = auth
        self._retry = retry
        self._shift_id = shift_id
        self._normalizer: Normalizer = normalizer if normalizer is not None else FileRowNormalizer()
        self._timeout_s = timeout_s
        self._last_successful_pull_utc: datetime | None = None
        self._last_status: HealthStatus = HealthStatus.UNKNOWN

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterator[CycleEvent]:
        yield from self._query(
            _CYCLE_QUERY, "cycles", since, until, self._normalizer.normalize_cycle
        )

    def get_delay_data(self, since: datetime, until: datetime) -> Iterator[DelayEvent]:
        yield from self._query(
            _DELAY_QUERY, "delays", since, until, self._normalizer.normalize_delay
        )

    def _post(
        self, query: str, since: datetime, until: datetime, *, retried_auth: bool = False
    ) -> dict[str, Any]:
        body = json.dumps(
            {"query": query, "variables": {"since": since.isoformat(), "until": until.isoformat()}}
        ).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._auth.credentials().token}",
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(self._endpoint, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                payload: dict[str, Any] = json.loads(response.read().decode("utf-8"))
                return payload
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and not retried_auth:
                refreshed = self._auth.refresh()
                if refreshed.is_err:
                    raise AuthenticationError(
                        f"credential refresh failed: {refreshed.error}"
                    ) from exc
                return self._post(query, since, until, retried_auth=True)
            if exc.code == 401:
                raise AuthenticationError(f"authentication failed for {self._endpoint}") from exc
            raise SourceUnavailableError(
                f"HTTP {exc.code} from {self._endpoint}: {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise SourceUnavailableError(f"could not reach {self._endpoint}: {exc.reason}") from exc

    def _query(
        self,
        query: str,
        field: str,
        since: datetime,
        until: datetime,
        normalize: Callable[[dict[str, Any]], _TEvent],
    ) -> Iterator[_TEvent]:
        try:
            payload = run_with_retry(lambda: self._post(query, since, until), self._retry)
            records = payload.get("data", {}).get(field, ())
            for record in records:
                raw = {**record, "shift_id": self._shift_id}
                try:
                    yield normalize(raw)
                except MappingError as exc:
                    _logger.warning("record failed to normalize and was skipped: %s", exc)
                    continue
            self._last_status = HealthStatus.HEALTHY
            self._last_successful_pull_utc = datetime.now(tz=timezone.utc)
        except (SourceUnavailableError, AuthenticationError):
            self._last_status = HealthStatus.UNHEALTHY
            raise

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            status=self._last_status,
            last_successful_pull_utc=self._last_successful_pull_utc,
        )
