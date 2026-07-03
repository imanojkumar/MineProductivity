"""The reference KPI Standard Library: one flagship KPI per category
(design spec §10.5, checklist "TonnesPerHour... and at least one
flagship KPI per remaining category"), plus the ``UTIL.OEE`` composite
worked example.

Import order matters here: ``@register`` (``kpis._registry.register``)
validates a KPI's dependency graph immediately at registration time
(design spec §26), so every module a later module's KPIs depend on must
be imported first. ``production`` (``PROD.TPH``) must precede
``cost`` (``COST.FuelPerTonne`` depends on it); ``utilization`` declares
its own internal ordering (``PhysicalAvailability``/``UseOfAvailability``/
``PerformanceRatio`` before ``OverallEquipmentEffectiveness``) within
the module itself.

Not part of the public API (design spec §8 does not list any concrete
flagship KPI by name, only the engine/metadata/category machinery) --
importing this subpackage is a side-effecting registration step,
performed once by ``mineproductivity.kpis``'s own ``__init__.py``.
"""

from __future__ import annotations

# Deliberately NOT a single alphabetized `from x import (...)` tuple:
# production must register PROD.TPH before cost (COST.FuelPerTonne
# depends on it) imports.
from mineproductivity.kpis.standard_library import production  # noqa: F401, I001
from mineproductivity.kpis.standard_library import utilization  # noqa: F401
from mineproductivity.kpis.standard_library import cost  # noqa: F401
from mineproductivity.kpis.standard_library import delay  # noqa: F401
from mineproductivity.kpis.standard_library import energy  # noqa: F401
from mineproductivity.kpis.standard_library import haulage  # noqa: F401
from mineproductivity.kpis.standard_library import maintenance  # noqa: F401
from mineproductivity.kpis.standard_library import quality  # noqa: F401
from mineproductivity.kpis.standard_library import safety  # noqa: F401

__all__ = [
    "cost",
    "delay",
    "energy",
    "haulage",
    "maintenance",
    "production",
    "quality",
    "safety",
    "utilization",
]
