"""``TwinSnapshot``: historical, point-in-time captures of a twin
(design spec §13) -- distinct from ``state.py``'s "current"
representation.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``events.AsOf`` is reused directly for the point-in-time reference
rather than defining a second "moment in time" concept (design spec
§3.4). ``TwinSnapshot`` is **not** a duplicate of
``events.EventSnapshot`` (spec 01): an ``EventSnapshot`` materializes
the *event store's* state (raw envelopes) as of a point in time, to
accelerate future replay; a ``TwinSnapshot`` materializes one *twin's
derived state* (already the product of folding events through
``_apply``) as of a point in time. The two serve different layers of
the stack and are not interchangeable (§31's recorded anti-pattern).
"""

from __future__ import annotations

import dataclasses

from mineproductivity.core import BaseValueObject
from mineproductivity.events import AsOf

from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.state import TwinState

__all__ = ["TwinSnapshot"]


@dataclasses.dataclass(frozen=True, slots=True)
class TwinSnapshot(BaseValueObject):
    """A point-in-time capture of one ``Twin``, for audit, historical
    query, and simulation-forking use -- distinct from ``TwinState``
    (design spec §12), which represents only the *current* condition.

    Examples
    --------
    >>> from datetime import datetime, timezone
    >>> snapshot = TwinSnapshot(
    ...     twin_id="CONV-7",
    ...     state=TwinState(
    ...         attributes={"belt_speed_mps": 3.1},
    ...         captured_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
    ...     ),
    ...     status=TwinStatus.SYNCHRONIZED,
    ...     as_of=AsOf(utc=datetime(2026, 7, 8, tzinfo=timezone.utc)),
    ... )
    >>> snapshot.twin_id
    'CONV-7'
    >>> snapshot.status
    <TwinStatus.SYNCHRONIZED: 'synchronized'>
    """

    twin_id: str
    state: TwinState
    status: TwinStatus
    as_of: AsOf
