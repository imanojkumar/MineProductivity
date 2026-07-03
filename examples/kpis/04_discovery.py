"""KPI discovery: introspecting ``REGISTRY`` -- listing every registered
KPI, filtering by namespace, and describing one KPI's full metadata
without ever reading its source code (KPI-as-object, Cookbook Part I Ch.
6: "every performance indicator [is] a discoverable, versioned, self
-describing object").

Run: python examples/kpis/04_discovery.py
"""

from __future__ import annotations

from mineproductivity.kpis import REGISTRY, CompositeKPI


def describe(code: str) -> None:
    """Print a KPI's full, governed metadata -- everything an engineer
    (or an AI agent) needs to trust a number without reading a formula
    buried in a script."""
    kpi_cls = REGISTRY.get(code)
    meta = kpi_cls.meta
    kind = "composite" if issubclass(kpi_cls, CompositeKPI) else "leaf"
    print(f"{meta.code} -- {meta.official_name} [{kind}, {meta.aggregation.value}]")
    print(f"  business purpose:      {meta.business_purpose}")
    print(f"  operational question:  {meta.operational_question}")
    print(f"  formula:               {meta.formula}")
    print(f"  unit:                  {meta.unit}")
    print(f"  direction:             {meta.direction.value}")
    print(f"  required events:       {', '.join(meta.required_events)}")
    if meta.dependencies:
        print(f"  dependencies:          {', '.join(meta.dependencies)}")


def main() -> None:
    print(f"--- 1. Every registered KPI code ({len(REGISTRY)} total) ---")
    for code in sorted(REGISTRY):
        print(f"  {code}")

    print()
    print("--- 2. Filter by namespace: everything in UTIL ---")
    util_codes = sorted(code for code in REGISTRY if code.startswith("UTIL."))
    print(f"  {util_codes}")

    print()
    print("--- 3. Filter to composite (DERIVED) KPIs only ---")
    composite_codes = sorted(
        code for code in REGISTRY if issubclass(REGISTRY.get(code), CompositeKPI)
    )
    print(f"  {composite_codes}")

    print()
    print("--- 4. Fully describe one flagship KPI without reading its source ---")
    describe("PROD.TPH")

    print()
    describe("UTIL.OEE")


if __name__ == "__main__":
    main()
