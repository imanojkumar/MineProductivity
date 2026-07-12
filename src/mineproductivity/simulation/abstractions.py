"""``SimulationModel``: the "Simulation-as-object" root every
registrable model type subclasses, and ``SimulationContext``, the
collaborator/evidence bundle a model's category method reasons over
(design spec §8).

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
``SimulationContext`` mirrors ``digital_twin.TwinContext``'s
collaborator-bundle shape (spec 08 §8) one layer up; evidence fields
carry ``kpis.KPIResult``/``analytics.AnalyticsResult``/
``decision.DecisionResult`` exactly as those packages define them --
read, never re-derived (design spec §3.2, the single most important
boundary in the governing specification). ``SimulationModel``
deliberately carries **no** shared abstract execution method: Monte
Carlo trials, discrete-event scheduling, and system-dynamics
integration are structurally different enough (§13-§15) that a single
shared signature would either lose information or need an
escape-hatch ``Any``-typed payload -- the identical reasoning
``decision.RootCauseAnalyzer``/``WhatIfEngine`` already applied when
each defined its own abstract method distinct from ``DecisionModel``'s
shared ``_decide`` (spec 07 §18, §19).
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from typing import Any, ClassVar

from mineproductivity.analytics import AnalyticsResult
from mineproductivity.decision import DecisionResult
from mineproductivity.events import EventStore
from mineproductivity.kpis import KPIResult

from mineproductivity.simulation.exceptions import SimulationValidationError
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata

__all__ = ["SimulationContext", "SimulationModel"]


def _enforce_category(
    cls: type["SimulationModel"], namespace: str, category: SimulationCategory
) -> None:
    """Shared namespace/category-conformance check the three
    ``SimulationModel`` category bases (design spec §13-§15) run from
    their own ``__init_subclass__`` hooks (§27) -- package-internal,
    mirroring ``digital_twin.categories._enforce_category`` in shape
    (spec 08 §23) and defined here because ``abstractions.py`` is the
    one module all three category bases already depend on (§6).
    Abstract intermediates that declare no ``meta`` of their own are
    skipped; a violation fails at class-definition (import) time."""
    if "meta" not in cls.__dict__:
        return
    code = cls.meta.code
    if not (code == namespace or code.startswith(f"{namespace}.")):
        raise SimulationValidationError(
            f"{cls.__name__}.meta.code {code!r} must fall in the {namespace!r} namespace"
        )
    if cls.meta.category is not category:
        raise SimulationValidationError(
            f"{cls.__name__}.meta.category must be {category!r}, got {cls.meta.category!r}"
        )


class SimulationContext:
    """Bundles the collaborators and evidence a ``SimulationModel`` may
    need -- the simulation-layer counterpart to
    ``digital_twin.TwinContext`` (spec 08 §8), one layer up. Carries
    the ``KPIResult``/``AnalyticsResult``/``DecisionResult`` evidence
    already gathered, plus access to ``events.EventStore`` for
    replay-based seeding (design spec §12). Evidence is gathered once,
    at the boundary, by the caller -- the executor never reaches back
    into a lower package on its own initiative (§4's runtime request
    flow).

    Examples
    --------
    >>> class _FakeStore: ...
    >>> context = SimulationContext(event_store=_FakeStore())
    >>> context.kpi_results
    ()
    >>> context.decision_results
    ()
    """

    def __init__(
        self,
        *,
        event_store: EventStore[Any],
        kpi_results: Sequence[KPIResult] = (),
        analytics_results: Sequence[AnalyticsResult] = (),
        decision_results: Sequence[DecisionResult] = (),
    ) -> None:
        self.event_store = event_store
        self.kpi_results = tuple(kpi_results)
        self.analytics_results = tuple(analytics_results)
        self.decision_results = tuple(decision_results)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(event_store={self.event_store!r}, "
            f"kpi_results={self.kpi_results!r}, "
            f"analytics_results={self.analytics_results!r}, "
            f"decision_results={self.decision_results!r})"
        )


class SimulationModel(ABC):
    """The root of every registrable simulation model type --
    'Simulation-as-object,' the direct counterpart of
    ``kpis.BaseKPI``/``analytics.AnalyticsModel``/``decision.DecisionModel``/
    ``digital_twin.Twin``, four/three/two/one layers down respectively.
    Deliberately carries no shared abstract execution method (see the
    module docstring); each category base (design spec §13-§15)
    declares its own.

    **Statelessness.** Every ``SimulationModel`` subclass, of every
    category, is stateless -- no instance attribute is mutated by any
    category method (design spec §29, §32); statefulness in this
    package lives entirely in ``SimulationRun`` (§10), never in a
    model implementation. A concrete ``MonteCarloModel`` in particular
    derives all randomness from the ``random_seed`` supplied per
    ``_trial`` call, never from internal generator state (§33, §34's
    recorded anti-pattern).
    """

    meta: ClassVar[SimulationMetadata]
