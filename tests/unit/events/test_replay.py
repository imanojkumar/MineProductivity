"""Tests for mineproductivity.events.replay."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from mineproductivity.events.exceptions import EventValidationError
from mineproductivity.events.replay import AsOf, ReplayHandle

NOW = datetime(2026, 6, 18, 6, tzinfo=timezone.utc)


class TestAsOf:
    def test_utc_only(self) -> None:
        as_of = AsOf(utc=NOW)
        assert as_of.utc == NOW
        assert as_of.scenario is None

    def test_scenario_only(self) -> None:
        as_of = AsOf(scenario="genesis")
        assert as_of.scenario == "genesis"
        assert as_of.utc is None

    def test_both_set(self) -> None:
        as_of = AsOf(utc=NOW, scenario="what-if")
        assert as_of.utc == NOW
        assert as_of.scenario == "what-if"

    def test_neither_set_rejected(self) -> None:
        with pytest.raises(EventValidationError):
            AsOf()


class TestReplayHandle:
    def test_empty_handle(self) -> None:
        handle: ReplayHandle[Any] = ReplayHandle(as_of=AsOf(scenario="genesis"), envelopes=())
        assert handle.envelopes == ()

    def test_get_returns_none_when_absent(self) -> None:
        handle: ReplayHandle[Any] = ReplayHandle(as_of=AsOf(scenario="genesis"), envelopes=())
        assert handle.get("missing") is None

    def test_get_finds_matching_envelope(self, cycle_envelope_factory) -> None:  # type: ignore[no-untyped-def]
        envelope = cycle_envelope_factory()
        handle: ReplayHandle[Any] = ReplayHandle(as_of=AsOf(utc=NOW), envelopes=(envelope,))
        found = handle.get(envelope.event_id.value)
        assert found is envelope
