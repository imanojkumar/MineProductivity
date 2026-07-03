"""``ResultCache``: memoizes ``KPIResult`` per ``(code, window, scope,
fingerprint)``.
"""

from __future__ import annotations

import dataclasses
import threading
from collections.abc import Callable, Mapping

from mineproductivity.kpis.result import KPIResult

__all__ = ["ResultCache"]


@dataclasses.dataclass(frozen=True, slots=True)
class _CacheKey:
    code: str
    window: str
    scope: tuple[tuple[str, str], ...]
    fingerprint: int


class ResultCache:
    """Memoizes :class:`~mineproductivity.kpis.result.KPIResult` per
    ``(code, window, scope, fingerprint)``.

    ``fingerprint`` is a caller-supplied, cheap proxy for "has anything
    relevant changed" -- :class:`~mineproductivity.kpis.engine.KPIEngine`
    passes the count of envelopes matching the query backing a given
    computation, so the cache key naturally changes the moment a new
    matching event lands (design spec §22's "invalidated automatically...
    never silently stale" guarantee), without requiring a new versioning
    API on the locked ``EventStore`` contract.

    Thread-safe: a single lock serializes reads-that-may-write, so
    concurrent :meth:`get_or_compute` calls for the same key never
    duplicate work or corrupt the cache -- the public contract only
    guarantees a consistent result, not this specific mechanism,
    mirroring ``registry.DiscoveryCache``'s concurrency contract.
    """

    def __init__(self) -> None:
        self._store: dict[_CacheKey, KPIResult] = {}
        self._lock = threading.Lock()

    def get_or_compute(
        self,
        code: str,
        window: str,
        scope: Mapping[str, str],
        fingerprint: int,
        compute: Callable[[], KPIResult],
    ) -> KPIResult:
        """Return the cached result for this key, computing (and
        caching) it via ``compute()`` on first access."""
        key = _CacheKey(
            code=code, window=window, scope=tuple(sorted(scope.items())), fingerprint=fingerprint
        )
        with self._lock:
            cached = self._store.get(key)
            if cached is not None:
                return cached
            result = compute()
            self._store[key] = result
            return result

    def invalidate(self, code: str | None = None) -> None:
        """Explicitly drop every cached result for ``code``, or every
        cached result if ``code`` is ``None``."""
        with self._lock:
            if code is None:
                self._store.clear()
            else:
                for key in [key for key in self._store if key.code == code]:
                    del self._store[key]

    def __len__(self) -> int:
        return len(self._store)
