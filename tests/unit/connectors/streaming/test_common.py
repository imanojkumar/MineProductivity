"""Tests for mineproductivity.connectors.streaming._common."""

from __future__ import annotations

from datetime import datetime, timezone

from mineproductivity.connectors.file._common import FileRowNormalizer
from mineproductivity.connectors.streaming._common import consume_message_source

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


class TestConsumeMessageSource:
    def test_messages_without_event_time_pass_through(self) -> None:
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source([_MESSAGE], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        )
        assert len(events) == 1

    def test_messages_with_in_window_event_time_pass(self) -> None:
        message = {**_MESSAGE, "event_time": "2026-06-25T06:00:00"}
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source([message], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        )
        assert len(events) == 1

    def test_messages_with_out_of_window_event_time_filtered(self) -> None:
        message = {**_MESSAGE, "event_time": "2026-07-01T06:00:00"}
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source([message], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        )
        assert events == []

    def test_unparseable_event_time_skipped(self) -> None:
        message = {**_MESSAGE, "event_time": "not-a-date"}
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source([message], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        )
        assert events == []

    def test_malformed_message_skipped_others_pass(self) -> None:
        good = _MESSAGE
        bad = {**_MESSAGE, "payload_t": "NOT_A_NUMBER"}
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source([bad, good], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        )
        assert len(events) == 1

    def test_shift_id_injected(self) -> None:
        normalizer = FileRowNormalizer()
        events = list(
            consume_message_source(
                [_MESSAGE], _SINCE, _UNTIL, "SHIFT-X", normalizer.normalize_cycle
            )
        )
        assert events[0].shift_id == "SHIFT-X"

    def test_lazy_generator(self) -> None:
        normalizer = FileRowNormalizer()
        result = consume_message_source([_MESSAGE], _SINCE, _UNTIL, "A", normalizer.normalize_cycle)
        assert not isinstance(result, list)
