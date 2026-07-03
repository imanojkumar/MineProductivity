"""Tests for mineproductivity.kpis.standard_library (the side-effecting
registration module and its import-order dependency rule)."""

from __future__ import annotations

import ast
from pathlib import Path

from mineproductivity.kpis import standard_library


class TestAllNineCategoriesRepresented:
    def test_all_lists_all_nine_submodules(self) -> None:
        assert set(standard_library.__all__) == {
            "cost",
            "delay",
            "energy",
            "haulage",
            "maintenance",
            "production",
            "quality",
            "safety",
            "utilization",
        }


class TestImportOrderRespectsDependencies:
    def test_production_is_imported_before_cost_in_source_order(self) -> None:
        """``cost.FuelPerTonne`` declares ``dependencies=("PROD.TPH",)`` and
        ``@register`` validates the dependency graph immediately at
        registration time -- so ``production`` (which defines
        ``PROD.TPH``) must be imported, and therefore registered, before
        ``cost``. A prior alphabetized single-tuple import broke this and
        was caught by the kpis smoke test; this is the regression test
        for that fix."""
        init_path = Path(standard_library.__file__)
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        imported_order = [
            node.names[0].name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "mineproductivity.kpis.standard_library"
        ]
        assert imported_order.index("production") < imported_order.index("cost")

    def test_reimporting_the_subpackage_does_not_re_raise(self) -> None:
        import importlib

        importlib.reload(standard_library)  # must not raise KPIVersionConflictError


class TestEveryFlagshipIsRegisteredAfterImport:
    def test_all_twelve_flagships_are_registered(self) -> None:
        """``REGISTRY`` is a process-level global other test modules also
        register fixture KPIs into within the same pytest session, so
        this checks the 12 known flagships are present as a subset
        rather than asserting an exact, session-order-dependent count."""
        from mineproductivity.kpis import REGISTRY

        expected = {
            "PROD.TPH",
            "UTIL.PA",
            "UTIL.UA",
            "UTIL.Performance",
            "UTIL.OEE",
            "MAINT.MTTR",
            "HAUL.TruckCycleTime",
            "DISP.TotalDelayHours",
            "ENERGY.FuelConsumed",
            "QUAL.OreProportion",
            "COST.FuelPerTonne",
            "SAFE.SpeedViolationCount",
        }
        assert expected <= set(REGISTRY)
