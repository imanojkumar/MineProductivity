"""The nine KPI category base classes, one per controlled namespace
family. Each contributes no behavior beyond documentation and a
namespace-conformance check (design spec §10.4); all real behavior lives
in :class:`~mineproductivity.kpis.base_kpi.BaseKPI` and is inherited
uniformly.
"""

from __future__ import annotations

from mineproductivity.kpis.categories.cost_kpi import CostKPI
from mineproductivity.kpis.categories.delay_kpi import DelayKPI
from mineproductivity.kpis.categories.energy_kpi import EnergyKPI
from mineproductivity.kpis.categories.haulage_kpi import HaulageKPI
from mineproductivity.kpis.categories.maintenance_kpi import MaintenanceKPI
from mineproductivity.kpis.categories.production_kpi import ProductionKPI
from mineproductivity.kpis.categories.quality_kpi import QualityKPI
from mineproductivity.kpis.categories.safety_kpi import SafetyKPI
from mineproductivity.kpis.categories.utilization_kpi import UtilizationKPI

__all__ = [
    "CostKPI",
    "DelayKPI",
    "EnergyKPI",
    "HaulageKPI",
    "MaintenanceKPI",
    "ProductionKPI",
    "QualityKPI",
    "SafetyKPI",
    "UtilizationKPI",
]
