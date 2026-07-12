"""Event replay integration (design spec §12): reconstruct an initial
``SimulationState`` from real event history.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``events.EventStore.replay(AsOf)``/``ReplayHandle`` are reused directly
-- ``seed_from_replay`` is a thin convenience wrapper over ``events``'
own replay mechanism, never a competing implementation of replay
itself (design spec §12, §34's recorded anti-pattern), exactly as
``digital_twin.TwinSynchronizer`` composes the same mechanism one
layer down for cold-start twin reconstruction (spec 08 §15). The
generic seed this function produces (replayed-event census plus the
last event's timestamp) is deliberately model-neutral: a concrete
``SimulationModel`` refines it into whatever model-specific attributes
its own methodology needs -- this package does not guess at them
(§3.1).
"""

from __future__ import annotations

from typing import Any

from mineproductivity.events import AsOf, EventStore

from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.state import SimulationState

__all__ = ["seed_from_replay"]


def seed_from_replay(store: EventStore[Any], as_of: AsOf) -> SimulationState:
    """Reconstructs an initial ``SimulationState`` from real event
    history via ``EventStore.replay(as_of)`` -- the concrete mechanism
    behind Business Objective 3 (design spec §2): 'simulate forward
    from last Tuesday's actual conditions' is ``seed_from_replay``
    followed by handing the result to a ``Scenario``.

    The reconstructed state is a deterministic census of the replayed
    history: ``events_replayed`` (total envelope count),
    ``event_counts`` (per payload-type counts, alphabetized), and --
    when any envelope exists -- ``last_event_time_utc`` (ISO 8601).
    ``simulated_time`` is ``as_of.utc`` when supplied, else the latest
    replayed envelope's ``event_time_utc``.

    Raises
    ------
    SimulationValidationError
        If ``as_of`` carries no ``utc`` and the replayed history is
        empty -- there is then no information from which to anchor
        ``simulated_time`` (a scenario-only ``AsOf`` over an empty
        history is a legitimately unanswerable seeding request).
    """
    handle = store.replay(as_of)
    counts: dict[str, int] = {}
    for envelope in handle.envelopes:
        type_name = type(envelope.payload).__name__
        counts[type_name] = counts.get(type_name, 0) + 1

    attributes: dict[str, Any] = {
        "events_replayed": len(handle.envelopes),
        "event_counts": dict(sorted(counts.items())),
    }
    latest = max((envelope.event_time_utc for envelope in handle.envelopes), default=None)
    if latest is not None:
        attributes["last_event_time_utc"] = latest.isoformat()

    simulated_time = as_of.utc if as_of.utc is not None else latest
    if simulated_time is None:
        raise SimulationValidationError(
            "seed_from_replay cannot anchor simulated_time: as_of carries no utc "
            "and the replayed history is empty"
        )
    return SimulationState(attributes=attributes, simulated_time=simulated_time)
