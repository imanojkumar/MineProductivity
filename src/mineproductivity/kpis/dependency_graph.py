"""``DependencyGraph``: a DAG over KPI codes, built from
``KPIMetadata.dependencies``.
"""

from __future__ import annotations

from collections.abc import Sequence

from mineproductivity.core import Maybe
from mineproductivity.registry import Registry

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.exceptions import KPICircularDependencyError

__all__ = ["DependencyGraph"]


class DependencyGraph:
    """A DAG over KPI codes, built from ``KPIMetadata.dependencies``.
    Topologically sorts so dependencies compute before dependents (Part
    III, Introduction: "the engine resolves them as a directed acyclic
    graph, computing dependencies before dependents").

    Topological order per code is memoized (design spec §9's
    ``kpis.dependency_graph._topo_cache``), invalidated only by an
    explicit :meth:`invalidate` call -- mirrors
    ``registry.DiscoveryCache``'s explicit-invalidation-only rule.
    """

    def __init__(self, registry: Registry[str, type[BaseKPI]]) -> None:
        self._registry = registry
        self._topo_cache: dict[str, Sequence[str]] = {}

    def topological_order(self, code: str) -> Sequence[str]:
        """Dependency-first order of every KPI code ``code`` transitively
        depends on, ending with ``code`` itself.

        Raises
        ------
        KPICircularDependencyError
            If resolving ``code``'s dependency chain finds a cycle.
        """
        cached = self._topo_cache.get(code)
        if cached is not None:
            return cached
        order: list[str] = []
        cycle = self._visit(code, visited=set(), stack=[], order=order)
        if cycle is not None:
            raise KPICircularDependencyError(f"circular KPI dependency: {' -> '.join(cycle)}")
        result = tuple(order)
        self._topo_cache[code] = result
        return result

    def detect_cycle(self) -> Maybe[Sequence[str]]:
        """Non-raising cycle detection across every code currently in the
        registry. ``KPIEngine``/the ``@register`` decorator converts a
        ``Some`` result into :class:`KPICircularDependencyError` at
        registration time, not at first execution."""
        visited: set[str] = set()
        for code in self._registry:
            if code in visited:
                continue
            order: list[str] = []
            cycle = self._visit(code, visited=visited, stack=[], order=order)
            if cycle is not None:
                return Maybe.some(tuple(cycle))
        return Maybe.nothing()

    def invalidate(self) -> None:
        """Explicitly drop every memoized topological order -- call after
        the registry changes (a new KPI registered)."""
        self._topo_cache.clear()

    def _visit(
        self, code: str, *, visited: set[str], stack: list[str], order: list[str]
    ) -> Sequence[str] | None:
        """Depth-first visit from ``code``, appending dependency-first
        order to ``order``. Returns the cycle (as a sequence of codes) if
        one is found reachable from ``code``, else ``None``."""
        if code in visited:
            return None
        if code in stack:
            return (*stack[stack.index(code) :], code)
        stack.append(code)
        kpi_cls = self._registry.get(code)
        for dependency_code in kpi_cls.meta.dependencies:
            cycle = self._visit(dependency_code, visited=visited, stack=stack, order=order)
            if cycle is not None:
                return cycle
        stack.pop()
        visited.add(code)
        order.append(code)
        return None
