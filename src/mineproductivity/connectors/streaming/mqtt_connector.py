"""``MqttConnector``: subscribes to a topic filter; yields one event per
published message.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime, timezone
from typing import Any, ClassVar, TypeVar

from mineproductivity.connectors.base import FMSConnector, IngestionMode
from mineproductivity.connectors.file._common import FileRowNormalizer
from mineproductivity.connectors.health import ConnectorHealth, HealthStatus
from mineproductivity.connectors.normalization import Normalizer
from mineproductivity.connectors.streaming._common import consume_message_source
from mineproductivity.events import CycleEvent, DelayEvent

__all__ = ["MqttConnector"]

_TEvent = TypeVar("_TEvent")


class MqttConnector(FMSConnector):
    """Subscribes to an MQTT topic filter; yields one event per published
    message. Follows the identical shape as
    :class:`~mineproductivity.connectors.streaming.kafka_connector.KafkaConnector`
    (see its docstring and this package's ``streaming/_common.py`` module
    docstring for why no broker client library is a dependency of this
    package).

    Not thread-safe for concurrent calls against the same instance
    (design spec §24).
    """

    name: ClassVar[str] = "mqtt"
    supported_modes: ClassVar[tuple[IngestionMode, ...]] = (IngestionMode.STREAMING,)

    def __init__(
        self,
        topic_filter: str,
        shift_id: str,
        *,
        cycle_source: Iterable[Mapping[str, Any]] | None = None,
        delay_source: Iterable[Mapping[str, Any]] | None = None,
        source_timezone: str = "UTC",
        normalizer: Normalizer | None = None,
    ) -> None:
        self._topic_filter = topic_filter
        self._shift_id = shift_id
        self._cycle_source = cycle_source
        self._delay_source = delay_source
        self._source_timezone = source_timezone
        self._normalizer: Normalizer = normalizer if normalizer is not None else FileRowNormalizer()
        self._last_successful_pull_utc: datetime | None = None
        self._message_count = 0

    def get_cycle_data(self, since: datetime, until: datetime) -> Iterator[CycleEvent]:
        if self._cycle_source is None:
            return
        yield from self._consume(self._cycle_source, since, until, self._normalizer.normalize_cycle)

    def get_delay_data(self, since: datetime, until: datetime) -> Iterator[DelayEvent]:
        if self._delay_source is None:
            return
        yield from self._consume(self._delay_source, since, until, self._normalizer.normalize_delay)

    def _consume(
        self,
        source: Iterable[Mapping[str, Any]],
        since: datetime,
        until: datetime,
        normalize: Callable[[dict[str, Any]], _TEvent],
    ) -> Iterator[_TEvent]:
        for event in consume_message_source(
            source, since, until, self._shift_id, normalize, source_timezone=self._source_timezone
        ):
            self._message_count += 1
            self._last_successful_pull_utc = datetime.now(tz=timezone.utc)
            yield event

    def health_check(self) -> ConnectorHealth:
        status = HealthStatus.HEALTHY if self._message_count > 0 else HealthStatus.UNKNOWN
        return ConnectorHealth(
            status=status,
            last_successful_pull_utc=self._last_successful_pull_utc,
            detail=f"{self._message_count} message(s) consumed from topic filter {self._topic_filter!r}",
        )
