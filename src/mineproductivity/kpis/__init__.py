"""``mineproductivity.kpis`` -- the metric backbone of MineProductivity.

Makes every performance indicator a discoverable, versioned, self
-describing object rather than a formula buried in a script or
spreadsheet cell (KPI-as-object, the root README's engineering
philosophy), guaranteeing the platform's central promise: two engineers,
two sites, or two AI agents each compute "availability" must get the
same number from the same events.

Implements ``docs/architecture/05_KPI_Engine_Design_Specification.md``
exactly. ``kpis`` depends on ``core``, ``ontology``, ``events``, and
``registry`` -- and MUST NEVER import ``connectors`` (the single most
load-bearing rule in the governing specification) -- see ``README.md``
for the full set of architectural rules this package must satisfy.

Everything documented here is part of the public API and can be imported
directly from ``mineproductivity.kpis``, e.g.::

    from mineproductivity.kpis import REGISTRY, KPIEngine
"""

from __future__ import annotations

from mineproductivity.kpis._registry import REGISTRY, register
from mineproductivity.kpis.base_kpi import BaseKPI
from mineproductivity.kpis.caching import ResultCache
from mineproductivity.kpis.categories import (
    CostKPI,
    DelayKPI,
    EnergyKPI,
    HaulageKPI,
    MaintenanceKPI,
    ProductionKPI,
    QualityKPI,
    SafetyKPI,
    UtilizationKPI,
)
from mineproductivity.kpis.composite import CompositeKPI
from mineproductivity.kpis.dependency_graph import DependencyGraph
from mineproductivity.kpis.engine import KPIEngine
from mineproductivity.kpis.exceptions import (
    KPIAggregationError,
    KPICircularDependencyError,
    KPINotFoundError,
    KPIValidationError,
    KPIVersionConflictError,
)
from mineproductivity.kpis.lifecycle import KPIStatus
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata
from mineproductivity.kpis.naming import KPIIdentifier, parse_identifier
from mineproductivity.kpis.result import KPIResult
from mineproductivity.kpis.windowing import CumulativeWindow, RollingWindow, Window

# Side-effecting: importing the standard library registers its flagship
# KPIs into REGISTRY, exactly as `connectors/__init__.py` registers its
# six built-in reference connectors. Import order relative to the
# symbols above matters: the standard library's own KPIs depend on the
# engine/metadata/category machinery already being fully defined.
from mineproductivity.kpis import standard_library as _standard_library  # noqa: E402

__all__ = [
    "Aggregation",
    "BaseKPI",
    "CompositeKPI",
    "CostKPI",
    "CumulativeWindow",
    "DelayKPI",
    "DependencyGraph",
    "DigitalMaturity",
    "Direction",
    "EnergyKPI",
    "HaulageKPI",
    "KPIAggregationError",
    "KPICircularDependencyError",
    "KPIEngine",
    "KPIIdentifier",
    "KPIMetadata",
    "KPINotFoundError",
    "KPIResult",
    "KPIStatus",
    "KPIValidationError",
    "KPIVersionConflictError",
    "MaintenanceKPI",
    "ProductionKPI",
    "QualityKPI",
    "REGISTRY",
    "ResultCache",
    "RollingWindow",
    "SafetyKPI",
    "UtilizationKPI",
    "Window",
    "parse_identifier",
    "register",
]

del _standard_library
