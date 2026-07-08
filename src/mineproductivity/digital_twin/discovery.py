"""Twin discovery (design spec §18) -- category/scope-based lookup over
currently-known twins.

Reuse audit (mandatory, before writing this module)
-----------------------------------------------------
Both factories are plain ``core.PredicateSpecification`` constructions,
composed with ``TwinRepository.list(specification)`` (design spec §20)
-- ``core.BaseRepository.list`` already accepts an optional
``BaseSpecification[TEntity]`` filter natively, so "which twins match
this category/scope" requires no new query mechanism, only two small,
named, reusable predicates. This is the same composable-specification
discovery pattern ``decision.RuleEngine`` (spec 07 §10) and
``events.EventFilter`` already established -- no third variant is
introduced. Neither function raises for an empty result (§18): that is
``core.BaseRepository.list``'s own already-correct behavior for a
specification matching nothing; ``TwinNotFoundError`` is reserved for
``TwinRepository.get(twin_id)``'s raising lookup by a specific,
expected identity, a fundamentally different question.
"""

from __future__ import annotations

from collections.abc import Mapping

from mineproductivity.core import BaseSpecification, PredicateSpecification

from mineproductivity.digital_twin.abstractions import Twin
from mineproductivity.digital_twin.metadata import TwinCategory

__all__ = ["by_category", "by_scope"]


def by_category(category: TwinCategory) -> BaseSpecification[Twin]:
    """A specification satisfied by every twin whose type's
    ``meta.category`` is ``category`` -- compose with
    ``TwinRepository.list()`` and ``&``/``|``/``~`` freely.

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    >>> repository.list(by_category(TwinCategory.CONVEYOR))
    []
    """
    return PredicateSpecification(lambda twin: twin.meta.category is category)


def by_scope(scope: Mapping[str, str]) -> BaseSpecification[Twin]:
    """A specification satisfied by every twin whose own ``scope``
    carries every key/value pair in ``scope`` (a subset match, mirroring
    ``decision.DecisionAuditTrail.query()``'s scope-filter semantics one
    layer down).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Twin, str] = InMemoryRepository()
    >>> repository.list(by_scope({"pit": "north"}))
    []
    """
    wanted = dict(scope)
    return PredicateSpecification(
        lambda twin: all(twin.scope.get(key) == value for key, value in wanted.items())
    )
