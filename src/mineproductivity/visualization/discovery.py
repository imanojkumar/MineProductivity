"""Dashboard discovery (design spec §27) -- theme/owner-based lookup
over currently-saved dashboards, mirroring ``agents.discovery``'s
identical pattern (spec 11 §23). ``by_owner`` is a convenience query
over already-visible dashboards, never an access-control boundary
(design spec §31) -- authorization belongs entirely to the packages
below this one.
"""

from __future__ import annotations

from mineproductivity.core import BaseSpecification, PredicateSpecification

from mineproductivity.visualization.dashboard import Dashboard

__all__ = ["by_owner", "by_theme"]


def by_theme(theme_code: str) -> BaseSpecification[Dashboard]:
    """A specification satisfied by every dashboard referencing
    ``theme_code`` -- compose with ``DashboardRepository.list()``
    freely; an empty result is a legitimate answer, never a raise
    (design spec §27).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
    >>> repository.list(by_theme("DARK_HIGH_CONTRAST"))
    []
    """
    return PredicateSpecification(lambda dashboard: dashboard.theme_code == theme_code)


def by_owner(owner: str) -> BaseSpecification[Dashboard]:
    """A specification satisfied by every dashboard owned by
    ``owner`` -- a convenience query only, never an access-control
    boundary (design spec §31).

    Examples
    --------
    >>> from mineproductivity.core import InMemoryRepository
    >>> repository: InMemoryRepository[Dashboard, str] = InMemoryRepository()
    >>> repository.list(by_owner("supervisor-a"))
    []
    """
    return PredicateSpecification(lambda dashboard: dashboard.owner == owner)
