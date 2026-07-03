"""Shared logic for streaming reference connectors
(:class:`~mineproductivity.connectors.streaming.kafka_connector.KafkaConnector`,
:class:`~mineproductivity.connectors.streaming.mqtt_connector.MqttConnector`).

Neither built-in streaming connector depends on a specific broker client
library (``kafka-python``, ``paho-mqtt``, ...) -- consistent with design
spec AD-CN-03's reasoning for keeping ``mineproductivity.connectors``
itself free of any specific vendor SDK, extended here to broker client
libraries. A caller supplies the live subscription as a plain
``Iterable[Mapping[str, Any]]`` (a real client's consumer iterator, or,
for tests/examples, an in-memory generator standing in for one); a real
``mineproductivity-kafka``/``mineproductivity-mqtt`` plugin package
would wrap the vendor client to produce this shape. Because this class
only ever pulls the next message when its own caller asks for the next
event, no unbounded buffering ever happens inside the connector itself
-- backpressure is inherent to the lazy-generator chain, not a separate
mechanism to implement (design spec §22).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime
from typing import Any, TypeVar

from mineproductivity.connectors.exceptions import MappingError
from mineproductivity.connectors.file._common import parse_source_datetime

__all__ = ["consume_message_source"]

_logger = logging.getLogger(__name__)
_TEvent = TypeVar("_TEvent")


def consume_message_source(
    source: Iterable[Mapping[str, Any]],
    since: datetime,
    until: datetime,
    shift_id: str,
    normalize: Callable[[dict[str, Any]], _TEvent],
    *,
    source_timezone: str = "UTC",
) -> Iterator[_TEvent]:
    """Consume ``source`` lazily, filtering by ``event_time`` against
    ``[since, until)`` when a message carries one (bounded-window
    replay/backfill use), and passing every message through unfiltered
    when it does not (pure live-streaming pass-through)."""
    for message in source:
        raw_time = message.get("event_time")
        if raw_time:
            try:
                event_time = parse_source_datetime(str(raw_time), source_timezone=source_timezone)
            except MappingError as exc:
                _logger.warning("unparseable event_time, message skipped: %s", exc)
                continue
            if not (since <= event_time < until):
                continue
        raw = {**message, "shift_id": shift_id}
        try:
            yield normalize(raw)
        except MappingError as exc:
            _logger.warning("message failed to normalize and was skipped: %s", exc)
            continue
