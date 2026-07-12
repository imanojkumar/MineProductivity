"""Optimization discovery (design spec §22) -- category/scope-based
lookup over currently-known runs, mirroring
``simulation.discovery``'s identical pattern (spec 09 §22), including
its disclosed resolution: the locked ``OptimizationRun`` shape carries
neither a category nor a scope field, so :func:`by_category` resolves
lazily through the published-problem store (§9) plus ``REGISTRY``
(§21) at ``list()`` time -- a run whose problem is unpublished or
whose model is unregistered simply does not match (never raises), and
:func:`by_scope` matches against the run's own ``problem_code``/
``status`` fields plus its open ``state.attributes`` mapping.
"""

from __future__ import annotations

from collections.abc import Mapping

from mineproductivity.core import BaseSpecification, PredicateSpecification

from mineproductivity.optimization._registry import REGISTRY
from mineproductivity.optimization.metadata import OptimizationCategory, OptimizationMetadata
from mineproductivity.optimization.problem import published_problem
from mineproductivity.optimization.run import OptimizationRun

__all__ = ["by_category", "by_scope"]


def _category_of(run: OptimizationRun) -> OptimizationCategory | None:
    problem = published_problem(run.problem_code)
    if problem is None:
        return None
    metadata = REGISTRY.metadata_for(problem.model_code)
    if metadata.is_nothing:
        return None
    found = metadata.unwrap()
    return found.category if isinstance(found, OptimizationMetadata) else None


def by_category(category: OptimizationCategory) -> BaseSpecification[OptimizationRun]:
    """A specification satisfied by every run whose published problem's
    registered model belongs to ``category`` -- compose with
    ``OptimizationRunRepository.list()`` freely; an empty result is a
    legitimate answer, never a raise (design spec §22).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    >>> repository.list(by_category(OptimizationCategory.LINEAR_PROGRAMMING))
    []
    """
    return PredicateSpecification(lambda run: _category_of(run) is category)


def by_scope(scope: Mapping[str, str]) -> BaseSpecification[OptimizationRun]:
    """A specification satisfied by every run carrying every key/value
    pair in ``scope``, resolved against ``problem_code``/``status``
    first and the open ``state.attributes`` mapping otherwise.

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[OptimizationRun, str] = InMemoryRepository()
    >>> repository.list(by_scope({"problem_code": "FLEET.NightShiftAllocation"}))
    []
    """
    wanted = dict(scope)

    def _matches(run: OptimizationRun) -> bool:
        for key, value in wanted.items():
            if key == "problem_code":
                observed: object = run.problem_code
            elif key == "status":
                observed = run.status.value
            else:
                observed = run.state.attributes.get(key)
            if observed != value:
                return False
        return True

    return PredicateSpecification(_matches)
