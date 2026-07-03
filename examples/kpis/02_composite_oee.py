"""Composite KPI execution: ``UTIL.OEE`` -- the engine resolves its
dependency graph (``UTIL.PA``, ``UTIL.UA``, ``UTIL.Performance``),
computes each leaf first, then combines them, all from one ``execute()``
call.

Run: python examples/kpis/02_composite_oee.py
"""

from __future__ import annotations

from _dataset import SHIFT_ID, build_engine

from mineproductivity.kpis import REGISTRY, DependencyGraph


def main() -> None:
    engine = build_engine()

    print("--- 1. UTIL.OEE's dependency graph is resolved automatically ---")
    graph = DependencyGraph(REGISTRY)
    order = graph.topological_order("UTIL.OEE")
    print(f"execution order: {' -> '.join(order)}")

    print()
    print("--- 2. One execute() call computes every dependency, then combines them ---")
    result = engine.execute("UTIL.OEE", window="shift", scope={"shift": SHIFT_ID})
    assert result.is_ok
    oee = result.unwrap()
    print(f"UTIL.OEE = {oee.value:.4f} (n={oee.n})")

    print()
    print("--- 3. The three components are independently inspectable too ---")
    for code in ("UTIL.PA", "UTIL.UA", "UTIL.Performance"):
        component = engine.execute(code, window="shift", scope={"shift": SHIFT_ID}).unwrap()
        print(
            f"{code:>18} = {component.value:.4f}"
            if component.value is not None
            else f"{code:>18} = None"
        )

    print()
    print("--- 4. A missing dependency's data propagates None, never a fabricated zero ---")
    empty = engine.execute("UTIL.OEE", window="shift", scope={"shift": "no-such-shift"}).unwrap()
    print(f"UTIL.OEE (no data) = {empty.value} warnings={empty.warnings}")


if __name__ == "__main__":
    main()
