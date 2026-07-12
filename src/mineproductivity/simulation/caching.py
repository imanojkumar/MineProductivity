"""``SimulationStateCache``: avoids redundant ``EventStore.replay()``
calls across repeated trials that all start from the identical
historical seed (design spec §26).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Deliberately **not** a reuse of ``kpis.ResultCache`` (spec 05 §10.8)
or ``digital_twin.TwinStateCache`` (spec 08 §22) -- the fourth
occurrence in this series of the same "shape looks similar, coupling
doesn't fit" reasoning (ADR-0009's recorded trade-off): this cache's
key shape ``(scenario_code, as_of)`` is coupled to replay-seeding
semantics specifically, not to KPI-result or twin-evidence-bundle
shapes. ``events.AsOf`` is reused verbatim as the point-in-time half
of the key -- already a frozen, hashable value object.

A cache miss is never an error: ``SimulationExecutor``/
``ExperimentRunner`` fall back to ``seed_from_replay`` (design spec
§12) directly whenever ``get()`` returns ``None`` -- a performance
optimization, never a correctness dependency, and never authoritative
for "what is this run's current state" (only
``SimulationRunRepository`` is, §26).
"""

from __future__ import annotations

import threading

from mineproductivity.events import AsOf

from mineproductivity.simulation.state import SimulationState

__all__ = ["SimulationStateCache"]


class SimulationStateCache:
    """Caches the ``SimulationState`` seeded for one
    ``(scenario_code, as_of)`` key (design spec §26).

    **Thread safety.** Reads/writes are keyed by
    ``(scenario_code, as_of)``; independent keys never contend beyond
    the single internal lock's brief critical section, and writes to
    the same key serialize on it (design spec §33) -- the same one-lock
    posture ``digital_twin.TwinStateCache`` already takes one layer
    down.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> cache = SimulationStateCache()
    >>> as_of = AsOf(utc=datetime(2026, 7, 8, tzinfo=timezone.utc))
    >>> cache.get("FLEET.NightShiftSurge", as_of) is None
    True
    >>> state = SimulationState(
    ...     attributes={"events_replayed": 3},
    ...     simulated_time=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ... )
    >>> cache.put("FLEET.NightShiftSurge", as_of, state)
    >>> cache.get("FLEET.NightShiftSurge", as_of) is state
    True
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, AsOf], SimulationState] = {}
        self._lock = threading.Lock()

    def get(self, scenario_code: str, as_of: AsOf) -> SimulationState | None:
        """The cached seed for ``(scenario_code, as_of)``, or ``None``
        -- a miss is never an error (design spec §26)."""
        with self._lock:
            return self._entries.get((scenario_code, as_of))

    def put(self, scenario_code: str, as_of: AsOf, state: SimulationState) -> None:
        """Store ``state`` under ``(scenario_code, as_of)``, replacing
        any previously-cached seed for the same key."""
        with self._lock:
            self._entries[(scenario_code, as_of)] = state

    def __repr__(self) -> str:
        with self._lock:
            return f"{type(self).__name__}(entries={len(self._entries)})"
