"""``ConversationTurn``/``ConversationContext``: dialogue-turn history
for one task (design spec §15).

Reuse audit: ``core.BaseValueObject`` reused verbatim. Genuinely new
to this series: no package below ``agents`` models multi-turn
dialogue, since kpis/analytics/decision/simulation/optimization are
each single-shot computations, not conversations. Distinct from
``AgentContext`` (§8), which bundles evidence FROM lower packages;
``ConversationContext`` accumulates the dialogue exchanged WITHIN this
package's own execution of one ``Task`` -- a record of what was said,
never a re-statement of what lower packages computed.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from mineproductivity.core import BaseValueObject

__all__ = ["ConversationContext", "ConversationTurn"]


@dataclasses.dataclass(frozen=True, slots=True)
class ConversationTurn(BaseValueObject):
    """One exchange in a task's dialogue -- ``speaker`` is an open
    string (an ``Agent``'s own code, ``"human"``, or a ``Tool``'s
    code), never a closed enum (design spec §15).

    Examples
    --------
    >>> from datetime import timezone
    >>> turn = ConversationTurn(
    ...     speaker="human", content="Proceed with plan B.",
    ...     occurred_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
    ... )
    >>> turn.speaker
    'human'
    """

    speaker: str
    content: str
    occurred_at: datetime


@dataclasses.dataclass(frozen=True, slots=True)
class ConversationContext(BaseValueObject):
    """An ordered history of ``ConversationTurn``\\ s for one ``Task``
    (design spec §15). Append-only in spirit: a new turn produces a
    new instance -- the same "represent a state change as a new
    instance" discipline ``Task.with_state()`` (§11) applies one level
    up.

    Examples
    --------
    >>> ConversationContext(task_id="TASK-1").turns
    ()
    """

    task_id: str
    turns: tuple[ConversationTurn, ...] = dataclasses.field(default=(), kw_only=True)
