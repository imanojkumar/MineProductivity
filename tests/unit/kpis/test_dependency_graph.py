"""Tests for mineproductivity.kpis.dependency_graph."""

from __future__ import annotations

import pytest

from mineproductivity.registry import Registry

from mineproductivity.kpis._registry import REGISTRY
from mineproductivity.kpis.categories.production_kpi import ProductionKPI
from mineproductivity.kpis.dependency_graph import DependencyGraph
from mineproductivity.kpis.exceptions import KPICircularDependencyError
from mineproductivity.kpis.metadata import Aggregation, DigitalMaturity, Direction, KPIMetadata


def _meta(code: str, dependencies: tuple[str, ...] = ()) -> KPIMetadata:
    return KPIMetadata(
        code=code,
        name=code,
        official_name=code,
        business_purpose="x",
        operational_question="x",
        business_meaning="x",
        formula="x",
        unit="x",
        dimensions=("Shift",),
        required_events=("CYCLE",),
        dependencies=dependencies,
        aggregation=Aggregation.ADDITIVE,
        direction=Direction.HIGHER_IS_BETTER,
        min_maturity=DigitalMaturity.L1_MANUAL,
        leading_or_lagging="lagging",
        operational_or_strategic="operational",
    )


def _leaf(code: str, dependencies: tuple[str, ...] = ()) -> type[ProductionKPI]:
    return type(
        code.replace(".", "_"),
        (ProductionKPI,),
        {"meta": _meta(code, dependencies), "_compute": lambda self, rows: None},
    )


class TestTopologicalOrder:
    def test_no_dependencies_orders_as_a_single_element(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-1")
        a = _leaf("PROD.A")
        registry.register("PROD.A", a, metadata=a.meta)
        graph = DependencyGraph(registry)
        assert graph.topological_order("PROD.A") == ("PROD.A",)

    def test_linear_chain_orders_dependencies_before_dependents(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-2")
        a = _leaf("PROD.A")
        b = _leaf("PROD.B", ("PROD.A",))
        c = _leaf("PROD.C", ("PROD.B",))
        for code, cls in (("PROD.A", a), ("PROD.B", b), ("PROD.C", c)):
            registry.register(code, cls, metadata=cls.meta)
        graph = DependencyGraph(registry)
        order = graph.topological_order("PROD.C")
        assert order == ("PROD.A", "PROD.B", "PROD.C")

    def test_diamond_dependency_each_shared_node_appears_once(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-3")
        a = _leaf("PROD.A")
        b = _leaf("PROD.B", ("PROD.A",))
        c = _leaf("PROD.C", ("PROD.A",))
        d = _leaf("PROD.D", ("PROD.B", "PROD.C"))
        for code, cls in (("PROD.A", a), ("PROD.B", b), ("PROD.C", c), ("PROD.D", d)):
            registry.register(code, cls, metadata=cls.meta)
        graph = DependencyGraph(registry)
        order = graph.topological_order("PROD.D")
        assert order.count("PROD.A") == 1
        assert order.index("PROD.A") < order.index("PROD.B") < order.index("PROD.D")
        assert order.index("PROD.A") < order.index("PROD.C") < order.index("PROD.D")

    def test_result_is_memoized(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-4")
        a = _leaf("PROD.A")
        registry.register("PROD.A", a, metadata=a.meta)
        graph = DependencyGraph(registry)
        first = graph.topological_order("PROD.A")
        second = graph.topological_order("PROD.A")
        assert first is second

    def test_real_registry_util_oee_orders_its_three_components_first(self) -> None:
        graph = DependencyGraph(REGISTRY)
        order = graph.topological_order("UTIL.OEE")
        assert order.index("UTIL.PA") < order.index("UTIL.OEE")
        assert order.index("UTIL.UA") < order.index("UTIL.OEE")
        assert order.index("UTIL.Performance") < order.index("UTIL.OEE")


class TestCycleDetection:
    def test_two_node_cycle_raises_with_the_cycle_path(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-cycle-2")
        a = _leaf("PROD.A", ("PROD.B",))
        b = _leaf("PROD.B", ("PROD.A",))
        registry.register("PROD.A", a, metadata=a.meta)
        registry.register("PROD.B", b, metadata=b.meta)
        graph = DependencyGraph(registry)
        with pytest.raises(KPICircularDependencyError, match="PROD.A"):
            graph.topological_order("PROD.A")

    def test_self_dependency_raises(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-self")
        a = _leaf("PROD.A", ("PROD.A",))
        registry.register("PROD.A", a, metadata=a.meta)
        graph = DependencyGraph(registry)
        with pytest.raises(KPICircularDependencyError):
            graph.topological_order("PROD.A")

    def test_detect_cycle_is_non_raising_and_finds_nothing_in_an_acyclic_registry(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-acyclic")
        a = _leaf("PROD.A")
        b = _leaf("PROD.B", ("PROD.A",))
        registry.register("PROD.A", a, metadata=a.meta)
        registry.register("PROD.B", b, metadata=b.meta)
        graph = DependencyGraph(registry)
        assert graph.detect_cycle().is_nothing

    def test_detect_cycle_finds_a_real_cycle(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-detect-cycle")
        a = _leaf("PROD.A", ("PROD.B",))
        b = _leaf("PROD.B", ("PROD.A",))
        registry.register("PROD.A", a, metadata=a.meta)
        registry.register("PROD.B", b, metadata=b.meta)
        graph = DependencyGraph(registry)
        outcome = graph.detect_cycle()
        assert outcome.is_some
        assert set(outcome.unwrap()) == {"PROD.A", "PROD.B"}

    def test_real_registry_has_no_cycle(self) -> None:
        graph = DependencyGraph(REGISTRY)
        assert graph.detect_cycle().is_nothing

    def test_outer_scan_skips_a_code_already_visited_via_an_earlier_codes_traversal(self) -> None:
        """Registered dependent-before-dependency (``PROD.D`` before its
        own dependency ``PROD.C``): visiting ``PROD.D`` first
        dependency-first-visits ``PROD.C`` too, marking it visited: when
        the outer scan then reaches ``PROD.C`` directly it must skip it
        rather than re-visiting, without ever falsely reporting a
        cycle."""
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-outer-skip")
        d = _leaf("PROD.D", ("PROD.C",))
        c = _leaf("PROD.C")
        registry.register("PROD.D", d, metadata=d.meta)
        registry.register("PROD.C", c, metadata=c.meta)
        graph = DependencyGraph(registry)
        assert graph.detect_cycle().is_nothing


class TestInvalidate:
    def test_invalidate_clears_the_memoized_cache(self) -> None:
        registry: Registry[str, type] = Registry(name="dep-graph-fixture-invalidate")
        a = _leaf("PROD.A")
        registry.register("PROD.A", a, metadata=a.meta)
        graph = DependencyGraph(registry)
        first = graph.topological_order("PROD.A")
        graph.invalidate()
        second = graph.topological_order("PROD.A")
        assert first == second
        assert first is not second
