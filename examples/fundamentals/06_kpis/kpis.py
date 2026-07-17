"""Lesson 06 -- KPIs: a metric is an object, not a formula in a spreadsheet.

Ask two engineers for "tonnes per hour" and you may get two numbers. Not
because either is bad at arithmetic, but because the formula, the unit,
the time basis, and the aggregation rule were never written down in a
place a machine could read.

MineProductivity makes every indicator a *governed object*: it carries
its own official name, business purpose, formula, unit, direction,
required events, dependencies, and -- critically -- its aggregation
rule. This lesson shows why that last field prevents one of the most
expensive mistakes in mining reporting: averaging a ratio.

Run: python examples/fundamentals/06_kpis/kpis.py
"""

from __future__ import annotations

from mineproductivity.kpis import REGISTRY, Aggregation, CompositeKPI, DependencyGraph, KPIResult
from mineproductivity.kpis.aggregation import combine_results
from mineproductivity.kpis.exceptions import KPIAggregationError


def describe(code: str) -> None:
    """Everything you need to trust a number -- without reading its source."""
    kpi_cls = REGISTRY.get(code)
    meta = kpi_cls.meta
    kind = "composite" if issubclass(kpi_cls, CompositeKPI) else "leaf"
    print(f"{meta.code} -- {meta.official_name}  [{kind}, aggregation={meta.aggregation.value}]")
    print(f"  question : {meta.operational_question}")
    print(f"  formula  : {meta.formula}")
    print(f"  unit     : {meta.unit}  (direction: {meta.direction.value})")
    print(f"  needs    : {', '.join(meta.required_events)}")
    if meta.dependencies:
        print(f"  depends  : {', '.join(meta.dependencies)}")


def main() -> None:
    print("--- 1. A KPI describes itself: governed metadata, machine-readable ---")
    describe("PROD.TPH")

    print()
    print("--- 2. Compute it: one CAT 793F's shift -- 40 cycles of 220 t ---")
    cycles = [{"payload_t": 220.0, "operating_h": 0.3} for _ in range(40)]
    tph = REGISTRY.get("PROD.TPH")().compute(cycles)
    print(f"PROD.TPH = {tph.value:.2f} {tph.unit} (n={tph.n} cycles)")

    print()
    print("--- 3. A composite KPI declares dependencies; the graph resolves them ---")
    describe("UTIL.OEE")
    order = DependencyGraph(REGISTRY).topological_order("UTIL.OEE")
    print(f"  resolution order: {' -> '.join(order)}")
    print("  (the engine computes each leaf first, then combines -- you never")
    print("   wire this by hand, and a cycle is rejected at registration time)")

    print()
    print("--- 4. Why aggregation is a governed field: NEVER average a ratio ---")
    # A-shift moved 15,600 t in 12 h (1,300 t/h). B-shift moved 6,600 t in 6 h
    # (1,100 t/h). What was the day's tonnes-per-hour?
    a_rows = [{"payload_t": 15_600.0, "operating_h": 12.0}]
    b_rows = [{"payload_t": 6_600.0, "operating_h": 6.0}]
    tph_kpi = REGISTRY.get("PROD.TPH")()
    a_shift = tph_kpi.compute(a_rows)
    b_shift = tph_kpi.compute(b_rows)
    assert a_shift.value is not None and b_shift.value is not None
    print(f"  A-shift: {a_shift.value:,.0f} t/h over 12 h")
    print(f"  B-shift: {b_shift.value:,.0f} t/h over 6 h")

    naive = (a_shift.value + b_shift.value) / 2
    print(f"  naive mean of the two rates : {naive:,.1f} t/h   <-- WRONG")

    print()
    print("  The framework refuses to make that mistake for you:")
    try:
        combine_results([a_shift, b_shift], Aggregation.RATIO, code="PROD.TPH", unit="t/h")
    except KPIAggregationError as exc:
        print(f"    KPIAggregationError: {exc}")

    print()
    print("  The only correct answer re-derives from the union of the raw rows:")
    correct = tph_kpi.compute([*a_rows, *b_rows])
    assert correct.value is not None
    print(f"    PROD.TPH over both shifts = {correct.value:,.1f} t/h   <-- correct")
    print("  (22,200 t moved in 18 h. The naive average over-reports by ~2.5%")
    print("   because it forgets the shifts were different lengths.)")

    print()
    print("--- 5. The rule is structural, not advisory ---")
    additive = combine_results(
        [
            KPIResult(code="PROD.Tonnes", value=15_600.0, unit="t", n=12),
            KPIResult(code="PROD.Tonnes", value=6_600.0, unit="t", n=6),
        ],
        Aggregation.ADDITIVE,
        code="PROD.Tonnes",
        unit="t",
    )
    assert additive.value is not None
    print(f"  ADDITIVE tonnes DO combine by summing: {additive.value:,.0f} t")
    print(
        f"  each KPI declares its own rule: PROD.TPH -> "
        f"{REGISTRY.get('PROD.TPH').meta.aggregation.value}"
    )
    print("  (you cannot 'accidentally' average a RATIO -- the metadata decides,")
    print("   not the caller's convenience. The error above is the guardrail.)")

    print()
    print("--- 6. The Standard Library is discoverable and self-documenting ---")
    composites = sorted(c for c in REGISTRY if issubclass(REGISTRY.get(c), CompositeKPI))
    print(f"  {len(REGISTRY)} KPIs registered; composite ones: {composites}")
    print("  (see examples/kpis/ for full KPIEngine execution over an event store)")


if __name__ == "__main__":
    main()
