"""``RestConnector``: pages through an HTTP API, yielding one event per
record per page.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from typing import Any, ClassVar, TypeVar
from urllib.parse import urlencode

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

__all__ = ["RestConnector"]

_logger = logging.getLogger(__name__)
_TEvent = TypeVar("_TEvent")


class RestConnector(FMSConnector):
    """Pages through an HTTP API using the standard library's
    :mod:`urllib` -- no third-party HTTP client dependency.

    Expects each page's JSON response shaped as ``{"records": [...],
    "has_more": bool}``, where each record has the same field shape
    :class:`~mineproductivity.connectors.file._common.FileRowNormalizer`
    already knows how to translate (reused here rather than duplicated).
    A ``401`` response triggers exactly one :meth:`AuthProvider.refresh`
    and retry before raising; a network or ``5xx`` failure is wrapped as
    :class:`~mineproductivity.connectors.exceptions.SourceUnavailableError`
    and handled by the injected :class:`RetryPolicy`.

    Not thread-safe for concurrent calls against the same instance;
    construct one instance per worker for concurrent ingestion (design
    spec §24). The injected ``auth``'s own :meth:`AuthProvider.refresh`
    remains safe to call concurrently across *different* connector
    instances sharing the same provider.
    """

    name: ClassVar[str] = "rest"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (
        IngestionMode.BATCH,
        IngestionMode.INCREMENTAL,
    )

    def __init__(
        self,
        base_url: str,
        auth: AuthProvider,
        retry: RetryPolicy,
        shift_id: str,
        *,
        normalizer: Normalizer | None = None,
        timeout_s: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = auth
        self._retry = retry
        self._shift_id = shift_id
        self._normalizer: Normalizer = normalizer if normalizer is not None else FileRowNormalizer()
        self._timeout_s = timeout_s
        self._last_successful_pull_utc: datetime | None = None
        self._last_status: HealthStatus = HealthStatus.UNKNOWN

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterator[CycleEvent]:
        yield from self._paginate("cycles", since, until, self._normalizer.normalize_cycle)

    def get_delay_data(self, since: datetime, until: datetime) -> Iterator[DelayEvent]:
        yield from self._paginate("delays", since, until, self._normalizer.normalize_delay)

    def _request_page(
        self,
        resource: str,
        since: datetime,
        until: datetime,
        page: int,
        *,
        retried_auth: bool = False,
    ) -> dict[str, Any]:
        query = urlencode({"since": since.isoformat(), "until": until.isoformat(), "page": page})
        url = f"{self._base_url}/{resource}?{query}"
        headers = {"Authorization": f"Bearer {self._auth.credentials().token}"}
        request = urllib.request.Request(url, headers=headers)
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
                return self._request_page(resource, since, until, page, retried_auth=True)
            if exc.code == 401:
                raise AuthenticationError(f"authentication failed for {url}") from exc
            raise SourceUnavailableError(f"HTTP {exc.code} from {url}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise SourceUnavailableError(f"could not reach {url}: {exc.reason}") from exc

    def _paginate(
        self,
        resource: str,
        since: datetime,
        until: datetime,
        normalize: Callable[[dict[str, Any]], _TEvent],
    ) -> Iterator[_TEvent]:
        page = 0
        try:
            while True:

                def _fetch(current_page: int = page) -> dict[str, Any]:
                    return self._request_page(resource, since, until, current_page)

                payload = run_with_retry(_fetch, self._retry)
                for record in payload.get("records", ()):
                    raw = {**record, "shift_id": self._shift_id}
                    try:
                        yield normalize(raw)
                    except MappingError as exc:
                        _logger.warning("record failed to normalize and was skipped: %s", exc)
                        continue
                self._last_status = HealthStatus.HEALTHY
                self._last_successful_pull_utc = datetime.now(tz=timezone.utc)
                if not payload.get("has_more", False):
                    return
                page += 1
        except (SourceUnavailableError, AuthenticationError):
            self._last_status = HealthStatus.UNHEALTHY
            raise

    def health_check(self) -> ConnectorHealth:
        return ConnectorHealth(
            status=self._last_status,
            last_successful_pull_utc=self._last_successful_pull_utc,
        )
