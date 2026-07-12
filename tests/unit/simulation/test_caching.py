"""Tests for mineproductivity.simulation.caching."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from mineproductivity.events import AsOf
from mineproductivity.simulation.caching import SimulationStateCache
from mineproductivity.simulation.state import SimulationState

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _state(events_replayed: int = 3) -> SimulationState:
    return SimulationState(attributes={"events_replayed": events_replayed}, simulated_time=_EPOCH)


class TestGetAndPut:
    def test_miss_returns_none_never_raises(self) -> None:
        assert SimulationStateCache().get("FLEET.Surge", AsOf(utc=_EPOCH)) is None

    def test_put_then_get_returns_the_cached_seed(self) -> None:
        cache = SimulationStateCache()
        state = _state()
        cache.put("FLEET.Surge", AsOf(utc=_EPOCH), state)
        assert cache.get("FLEET.Surge", AsOf(utc=_EPOCH)) is state

    def test_key_is_scenario_code_and_as_of_jointly(self) -> None:
        cache = SimulationStateCache()
        cache.put("FLEET.Surge", AsOf(utc=_EPOCH), _state())
        assert cache.get("FLEET.Other", AsOf(utc=_EPOCH)) is None
        assert cache.get("FLEET.Surge", AsOf(utc=_EPOCH + timedelta(hours=1))) is None

    def test_scenario_as_of_keys_are_distinct_from_utc_keys(self) -> None:
        cache = SimulationStateCache()
        cache.put("FLEET.Surge", AsOf(scenario="what-if"), _state())
        assert cache.get("FLEET.Surge", AsOf(scenario="what-if")) is not None
        assert cache.get("FLEET.Surge", AsOf(utc=_EPOCH)) is None

    def test_put_replaces_the_previous_entry_for_the_same_key(self) -> None:
        cache = SimulationStateCache()
        cache.put("FLEET.Surge", AsOf(utc=_EPOCH), _state(1))
        replacement = _state(2)
        cache.put("FLEET.Surge", AsOf(utc=_EPOCH), replacement)
        assert cache.get("FLEET.Surge", AsOf(utc=_EPOCH)) is replacement

    def test_repr_includes_entry_count(self) -> None:
        cache = SimulationStateCache()
        cache.put("FLEET.Surge", AsOf(utc=_EPOCH), _state())
        assert "1" in repr(cache)


class TestConcurrency:
    def test_independent_keys_do_not_interfere_under_concurrent_writes(self) -> None:
        cache = SimulationStateCache()
        seeds = {f"SCN-{index}": _state(index + 1) for index in range(8)}

        def _put_many(code: str) -> None:
            for _ in range(100):
                cache.put(code, AsOf(utc=_EPOCH), seeds[code])

        threads = [threading.Thread(target=_put_many, args=(code,)) for code in seeds]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        for code, seed in seeds.items():
            assert cache.get(code, AsOf(utc=_EPOCH)) is seed
