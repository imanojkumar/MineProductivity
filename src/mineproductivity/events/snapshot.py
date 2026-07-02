"""``EventSnapshot``: a materialized checkpoint accelerating future replay."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

from mineproductivity.core import BaseValueObject

from mineproductivity.events.envelope import EventEnvelope
from mineproductivity.events.replay import AsOf

__all__ = ["EventSnapshot"]


@dataclasses.dataclass(frozen=True, slots=True)
class EventSnapshot(BaseValueObject):
    """A materialized checkpoint of a store's logical state as of ``as_of``.

    Snapshotting is a performance extension point, never a correctness
    requirement: a conformant :class:`~mineproductivity.events.store.EventStore`
    implementation MAY refuse to produce snapshots (falling back to full
    replay from genesis) and still be conformant, provided replay
    produces an identical result. The equivalence law a conformant
    snapshot strategy must satisfy is::

        replay(as_of) == fold(query(since=snapshot.as_of, until=as_of), initial=snapshot.state)

    Examples
    --------
    >>> snapshot = EventSnapshot(as_of=AsOf(scenario="genesis"), state={})
    >>> snapshot.state
    {}
    """

    as_of: AsOf
    state: Mapping[str, EventEnvelope[Any]]
