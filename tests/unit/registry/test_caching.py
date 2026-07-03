"""Tests for mineproductivity.registry.caching."""

from __future__ import annotations

import threading
from collections.abc import Sequence

from mineproductivity.core import Result
from mineproductivity.registry.caching import DiscoveryCache
from mineproductivity.registry.entry_point import EntryPointDiscovery, EntryPointSpec


class _CountingDiscovery(EntryPointDiscovery):
    def __init__(self) -> None:
        self.calls = 0

    def discover(self, spec: EntryPointSpec) -> Result[Sequence[str]]:
        self.calls += 1
        return Result.ok((f"result-for-{spec.group}",))


class TestGetOrDiscover:
    def test_first_call_invokes_discovery(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec = EntryPointSpec(group="g", target_registry="t")

        result = cache.get_or_discover(spec, discovery)

        assert discovery.calls == 1
        assert result.value == ("result-for-g",)

    def test_second_call_for_same_spec_is_memoized(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec = EntryPointSpec(group="g", target_registry="t")

        cache.get_or_discover(spec, discovery)
        cache.get_or_discover(spec, discovery)
        cache.get_or_discover(spec, discovery)

        assert discovery.calls == 1

    def test_different_specs_each_trigger_their_own_discovery(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec_a = EntryPointSpec(group="a", target_registry="t")
        spec_b = EntryPointSpec(group="b", target_registry="t")

        cache.get_or_discover(spec_a, discovery)
        cache.get_or_discover(spec_b, discovery)

        assert discovery.calls == 2

    def test_concurrent_calls_for_the_same_spec_trigger_exactly_one_discovery(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec = EntryPointSpec(group="g", target_registry="t")

        threads = [
            threading.Thread(target=cache.get_or_discover, args=(spec, discovery))
            for _ in range(16)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert discovery.calls == 1


class TestInvalidate:
    def test_invalidate_specific_spec_forces_rediscovery(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec = EntryPointSpec(group="g", target_registry="t")

        cache.get_or_discover(spec, discovery)
        cache.invalidate(spec)
        cache.get_or_discover(spec, discovery)

        assert discovery.calls == 2

    def test_invalidate_all_forces_rediscovery_of_every_spec(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec_a = EntryPointSpec(group="a", target_registry="t")
        spec_b = EntryPointSpec(group="b", target_registry="t")

        cache.get_or_discover(spec_a, discovery)
        cache.get_or_discover(spec_b, discovery)
        cache.invalidate()
        cache.get_or_discover(spec_a, discovery)
        cache.get_or_discover(spec_b, discovery)

        assert discovery.calls == 4

    def test_invalidate_never_invoked_implicitly(self) -> None:
        cache = DiscoveryCache()
        discovery = _CountingDiscovery()
        spec = EntryPointSpec(group="g", target_registry="t")

        for _ in range(5):
            cache.get_or_discover(spec, discovery)

        assert discovery.calls == 1
