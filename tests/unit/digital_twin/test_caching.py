"""Tests for mineproductivity.digital_twin.caching."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from mineproductivity.digital_twin.abstractions import TwinContext
from mineproductivity.digital_twin.caching import TwinStateCache
from mineproductivity.events import AsOf

_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


class _FakeStore:
    """Duck-typed ``EventStore`` stand-in."""


def _context() -> TwinContext:
    return TwinContext(event_store=_FakeStore())


class TestGetAndPut:
    def test_miss_returns_none_never_raises(self) -> None:
        """Design spec §22: a cache miss is never an error condition --
        the caller falls back to direct evidence re-assembly."""
        assert TwinStateCache().get("CONV-7", AsOf(utc=_EPOCH)) is None

    def test_put_then_get_returns_the_cached_context(self) -> None:
        cache = TwinStateCache()
        context = _context()
        cache.put("CONV-7", AsOf(utc=_EPOCH), context)
        assert cache.get("CONV-7", AsOf(utc=_EPOCH)) is context

    def test_key_is_twin_id_and_as_of_jointly(self) -> None:
        cache = TwinStateCache()
        cache.put("CONV-7", AsOf(utc=_EPOCH), _context())
        assert cache.get("CONV-8", AsOf(utc=_EPOCH)) is None
        assert cache.get("CONV-7", AsOf(utc=_EPOCH + timedelta(hours=1))) is None

    def test_scenario_as_of_keys_are_distinct_from_utc_keys(self) -> None:
        cache = TwinStateCache()
        cache.put("CONV-7", AsOf(scenario="what-if-belt-upgrade"), _context())
        assert cache.get("CONV-7", AsOf(scenario="what-if-belt-upgrade")) is not None
        assert cache.get("CONV-7", AsOf(utc=_EPOCH)) is None

    def test_put_replaces_the_previous_entry_for_the_same_key(self) -> None:
        cache = TwinStateCache()
        first, second = _context(), _context()
        cache.put("CONV-7", AsOf(utc=_EPOCH), first)
        cache.put("CONV-7", AsOf(utc=_EPOCH), second)
        assert cache.get("CONV-7", AsOf(utc=_EPOCH)) is second

    def test_repr_includes_entry_count(self) -> None:
        cache = TwinStateCache()
        cache.put("CONV-7", AsOf(utc=_EPOCH), _context())
        assert "1" in repr(cache)


class TestConcurrency:
    def test_independent_keys_do_not_interfere_under_concurrent_writes(self) -> None:
        """Design spec §30: reads/writes keyed by ``(twin_id, as_of)``;
        independent keys never contend."""
        cache = TwinStateCache()
        contexts = {f"TWIN-{index}": _context() for index in range(8)}

        def _put_many(twin_id: str) -> None:
            for _ in range(100):
                cache.put(twin_id, AsOf(utc=_EPOCH), contexts[twin_id])

        threads = [threading.Thread(target=_put_many, args=(twin_id,)) for twin_id in contexts]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        for twin_id, context in contexts.items():
            assert cache.get(twin_id, AsOf(utc=_EPOCH)) is context
