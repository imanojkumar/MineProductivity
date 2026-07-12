"""Simulation discovery (design spec §22) -- category/scope-based
lookup over currently-known runs.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Both factories are plain ``core.PredicateSpecification`` constructions,
composed with ``SimulationRunRepository.list(specification)`` (design
spec §24), mirroring ``digital_twin.discovery``'s identical pattern
(spec 08 §18) -- no new query mechanism. Neither function raises for
an empty result (§22).

**Disclosed spec-internal imprecision, resolved minimally.** Unlike a
``Twin`` (whose ``meta.category``/``scope`` live on the instance,
spec 08 §18), the locked ``SimulationRun`` shape (§10) carries only
``scenario_code``/``state``/``status`` -- neither a category nor a
scope field, and §6's own module table names only ``core`` and
``run.py`` as this module's dependencies. The only information path
from a bare run to a ``SimulationCategory`` without adding a field to
the locked ``SimulationRun`` shape is: ``run.scenario_code`` -> the
published ``Scenario``'s ``model_code`` (§9's governance store) ->
``REGISTRY``'s registered metadata (§21). :func:`by_category`
therefore resolves lazily through those two already-public lookups at
``list()`` time -- a run whose scenario is unpublished or whose model
is unregistered simply does not match (the §22 empty-result-never-
raise convention), and the extra imports beyond §6's two-line
dependency list are disclosed here as the smallest resolution that
touches no locked shape. :func:`by_scope` matches its key/value
constraints against the run's own fields (``scenario_code``,
``status``) and its ``state.attributes`` -- the open per-run mapping
§6's ``state.py`` entry designates for exactly this kind of
model-specific dimension.
"""

from __future__ import annotations

from collections.abc import Mapping

from mineproductivity.core import BaseSpecification, PredicateSpecification

from mineproductivity.simulation._registry import REGISTRY
from mineproductivity.simulation.metadata import SimulationCategory, SimulationMetadata
from mineproductivity.simulation.run import SimulationRun
from mineproductivity.simulation.scenario import published_scenario

__all__ = ["by_category", "by_scope"]


def _category_of(run: SimulationRun) -> SimulationCategory | None:
    scenario = published_scenario(run.scenario_code)
    if scenario is None:
        return None
    metadata = REGISTRY.metadata_for(scenario.model_code)
    if metadata.is_nothing:
        return None
    found = metadata.unwrap()
    return found.category if isinstance(found, SimulationMetadata) else None


def by_category(category: SimulationCategory) -> BaseSpecification[SimulationRun]:
    """A specification satisfied by every run whose published
    scenario's registered model belongs to ``category`` -- compose with
    ``SimulationRunRepository.list()`` and ``&``/``|``/``~`` freely.
    A run whose scenario is unpublished, or whose model is
    unregistered, never matches (and never raises, design spec §22).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    >>> repository.list(by_category(SimulationCategory.MONTE_CARLO))
    []
    """
    return PredicateSpecification(lambda run: _category_of(run) is category)


def by_scope(scope: Mapping[str, str]) -> BaseSpecification[SimulationRun]:
    """A specification satisfied by every run carrying every key/value
    pair in ``scope``, resolved against the run's own ``scenario_code``
    /``status`` fields first and its open ``state.attributes`` mapping
    otherwise (a subset match, mirroring ``digital_twin.by_scope``'s
    semantics one layer down).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[SimulationRun, str] = InMemoryRepository()
    >>> repository.list(by_scope({"scenario_code": "FLEET.NightShiftSurge"}))
    []
    """
    wanted = dict(scope)

    def _matches(run: SimulationRun) -> bool:
        for key, value in wanted.items():
            if key == "scenario_code":
                observed: object = run.scenario_code
            elif key == "status":
                observed = run.status.value
            else:
                observed = run.state.attributes.get(key)
            if observed != value:
                return False
        return True

    return PredicateSpecification(_matches)
