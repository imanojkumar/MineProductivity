"""The KPI registry -- a typed specialization of the generic Registry
Framework mechanism (design spec AD-KP-06), factored into its own
internal module so ``kpis/__init__.py`` can auto-register the standard
library without a circular import (each standard-library module needs
``register`` too).

``register`` additionally proves ``KPICircularDependencyError`` at
*registration* time (never deferred to first execution, design spec
§26): once a KPI is added to ``REGISTRY``, its topological order is
computed immediately, and any cycle found aborts the registration.
"""

from __future__ import annotations

from mineproductivity.registry import Registry

from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.dependency_graph import DependencyGraph
from mineproductivity.kpis.exceptions import KPIValidationError, KPIVersionConflictError

__all__ = ["REGISTRY", "register"]

REGISTRY: Registry[str, type[BaseKPI]] = Registry(name="kpis")

_GRAPH = DependencyGraph(REGISTRY)


def register(cls: type[BaseKPI]) -> type[BaseKPI]:
    """Register ``cls`` into :data:`REGISTRY`, keyed by ``cls.meta.code``.

    Raises
    ------
    KPIValidationError
        If ``cls.meta`` itself is invalid (propagated from construction
        -- ``KPIMetadata.validate()`` already ran when ``cls.meta`` was
        assigned as a class attribute).
    KPIVersionConflictError
        If ``cls.meta.code`` is already registered -- a KPI code is a
        public contract; a genuine new meaning requires a MAJOR version
        bump under review, never silent re-registration (design spec
        §17, §20).
    KPICircularDependencyError
        If registering ``cls`` completes a dependency cycle -- checked
        immediately, not deferred to first :meth:`~mineproductivity.kpis.engine.KPIEngine.execute` call.
    """
    if not cls.meta.code:
        raise KPIValidationError(f"{cls.__name__}.meta.code must not be empty")

    result = REGISTRY.register(cls.meta.code, cls, metadata=cls.meta)
    if result.is_err:
        raise KPIVersionConflictError(
            f"KPI code {cls.meta.code!r} is already registered; changing what it means "
            f"requires a MAJOR version bump under review, not re-registration"
        )

    _GRAPH.invalidate()
    _GRAPH.topological_order(
        cls.meta.code
    )  # raises KPICircularDependencyError at registration time

    return cls
