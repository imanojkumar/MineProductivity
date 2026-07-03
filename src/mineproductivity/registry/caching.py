"""``DiscoveryCache``: memoizes entry-point discovery per process."""

from __future__ import annotations

import threading
from collections.abc import Sequence

from mineproductivity.core import Result

from mineproductivity.registry.entry_point import EntryPointDiscovery, EntryPointSpec

__all__ = ["DiscoveryCache"]


class DiscoveryCache:
    """Memoizes :meth:`EntryPointDiscovery.discover` results per
    :class:`EntryPointSpec` for the lifetime of the process --
    entry-point scanning touches the filesystem/importlib metadata and
    is not free to repeat on every lookup (design spec §22).

    Invalidated only by an explicit call to :meth:`invalidate`, never
    implicitly -- e.g. a test harness that installs a plugin mid-process
    must call ``invalidate()`` itself to see it.

    A single lock serializes ``get_or_discover`` calls, so concurrent
    calls for the *same* spec are guaranteed to trigger exactly one
    underlying discovery pass (design spec §25); the public contract
    only guarantees that result, not this specific locking strategy.
    """

    def __init__(self) -> None:
        self._cache: dict[EntryPointSpec, Result[Sequence[str]]] = {}
        self._lock = threading.Lock()

    def get_or_discover(
        self, spec: EntryPointSpec, discovery: EntryPointDiscovery
    ) -> Result[Sequence[str]]:
        """Return the cached discovery result for ``spec``, computing and
        caching it via ``discovery.discover(spec)`` on first access."""
        with self._lock:
            cached = self._cache.get(spec)
            if cached is not None:
                return cached
            result = discovery.discover(spec)
            self._cache[spec] = result
            return result

    def invalidate(self, spec: EntryPointSpec | None = None) -> None:
        """Explicitly drop the cached result for ``spec``, or every
        cached result if ``spec`` is ``None``."""
        with self._lock:
            if spec is None:
                self._cache.clear()
            else:
                self._cache.pop(spec, None)
