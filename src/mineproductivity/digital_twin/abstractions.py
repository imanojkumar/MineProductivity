"""``Twin``: the "Twin-as-object" root every registrable twin type
subclasses, and ``TwinContext``, the collaborator/evidence bundle a
concrete twin's ``_apply`` reasons over (design spec §8).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``core.BaseEntity[str]`` is reused by **literal inheritance** -- the
strongest reuse available in this series (design spec §3.4): unlike
``kpis.BaseKPI``/``analytics.AnalyticsModel``/``decision.DecisionModel``
(each deliberately stateless), a ``Twin`` genuinely is an
identity-bearing entity whose state evolves over time, exactly the
shape ``BaseEntity``'s own docstring anticipates ("representing a state
change means producing a new instance... consistent with the platform's
event-first architecture"). ``__eq__``/``__hash__`` are inherited
unchanged (identity-based on ``id``, ignoring ``state``/``status``) --
no override anywhere in this package. ``TwinContext`` mirrors
``decision.DecisionContext``'s collaborator-bundle shape (spec 07 §8)
one layer up, extended with ``decision_results`` since ``digital_twin``
is the first package to consume Decision's own outputs directly.
Evidence fields carry ``kpis.KPIResult``/``analytics.AnalyticsResult``/
``decision.DecisionResult`` exactly as those packages define them --
read, never re-derived (§3.2, the single most important boundary in
the governing specification).
"""

from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any, ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.core import BaseEntity
from mineproductivity.decision import DecisionResult
from mineproductivity.events import AsOf, BaseEvent, EventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.digital_twin.lifecycle import TwinStatus
from mineproductivity.digital_twin.metadata import TwinMetadata
from mineproductivity.digital_twin.state import TwinState

__all__ = ["Twin", "TwinContext"]


@dataclasses.dataclass(frozen=True, slots=True, eq=False)
class Twin(BaseEntity[str], ABC):
    """The root of every registrable twin type -- 'Twin-as-object,' the
    direct counterpart of ``kpis.BaseKPI``/``analytics.AnalyticsModel``/
    ``decision.DecisionModel``, one/two/three layers down respectively.
    Unlike those three (deliberately stateless, spec 06 §8, spec 07 §8),
    ``Twin`` subclasses ``core.BaseEntity[str]`` directly: ``id``
    (inherited) is the twin's identity, and -- per ``BaseEntity``'s own
    documented contract -- representing a state change means producing
    a NEW ``Twin`` instance via :meth:`with_state`, never mutating
    fields in place. This mirrors the platform's event-first philosophy
    exactly: a twin's state is a projection of the event stream, not a
    mutable record (design spec §3.3).

    ``scope`` is set once at provisioning time and is immutable
    thereafter (frozen into a read-only mapping at construction) -- a
    twin that starts representing a different real-world instance is a
    new ``Twin`` (a new ``id``), never the same twin re-scoped in place
    (design spec §9, §31).

    **Thread safety.** ``Twin`` instances are immutable -- trivially
    safe to read and share across threads; no locking is ever needed to
    read a twin's ``state``/``status`` (design spec §29). A concrete
    ``_apply`` implementation MUST itself be safe to call concurrently
    for *different* ``id``\\ s on any shared collaborators it closes
    over (§30).
    """

    meta: ClassVar[TwinMetadata]
    scope: Mapping[str, str]
    state: TwinState
    status: TwinStatus = dataclasses.field(default=TwinStatus.PROVISIONED)

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope", MappingProxyType(dict(self.scope)))

    @abstractmethod
    def _apply(self, events: Sequence[BaseEvent], *, context: TwinContext) -> TwinState:
        """Pure function: current state + new events (+ whatever
        evidence ``context`` carries) -> next ``TwinState``. MUST NOT
        raise for a legitimately empty ``events`` batch -- return
        ``self.state`` unchanged, exactly the 'qualify, don't coerce'
        rule ``kpis.BaseKPI``, ``analytics.AnalyticsModel``, and
        ``decision.DecisionModel`` already established."""

    def with_state(self, state: TwinState, *, status: TwinStatus | None = None) -> Twin:
        """Returns a NEW ``Twin`` instance with ``state`` (and
        optionally ``status``) replacing the current ones -- the
        ``dataclasses.replace``-style helper ``core.BaseEntity``'s own
        docstring anticipates for representing a state change."""
        return dataclasses.replace(
            self, state=state, status=status if status is not None else self.status
        )


class TwinContext:
    """Bundles the collaborators and evidence a ``Twin``'s ``_apply``
    may need -- the digital-twin-layer counterpart to
    ``decision.DecisionContext`` (spec 07 §8), one layer up, extended
    with ``decision_results`` since ``digital_twin`` is the first
    package to consume Decision's own outputs directly (design spec §8).

    Examples
    --------
    >>> class _FakeStore: ...
    >>> context = TwinContext(event_store=_FakeStore())
    >>> context.kpi_results
    ()
    >>> context.as_of is None
    True
    """

    def __init__(
        self,
        *,
        event_store: EventStore[Any],
        kpi_results: Sequence[KPIResult] = (),
        analytics_results: Sequence[AnalyticsResult] = (),
        decision_results: Sequence[DecisionResult] = (),
        as_of: AsOf | None = None,
    ) -> None:
        self.event_store = event_store
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.decision_results = tuple(decision_results)
        self.as_of = as_of

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event_store={self.event_store!r}, "
            f"kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, "
            f"decision_results={self.decision_results!r}, as_of={self.as_of!r})"
        )
