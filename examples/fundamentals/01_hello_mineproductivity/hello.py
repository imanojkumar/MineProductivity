"""Lesson 01 -- Hello, MineProductivity.

Your first contact with the framework: confirm the install, then compute
a real mining KPI (tonnes per hour for one haul truck over one shift)
without writing a single formula yourself.

The point of this lesson is not the arithmetic. It is that
``PROD.TPH`` is a *governed object* you look up by name -- carrying its
own units, provenance, and validity rules -- rather than a number you
re-derive in every script and spreadsheet.

Run: python examples/fundamentals/01_hello_mineproductivity/hello.py
"""

from __future__ import annotations

import mineproductivity
from mineproductivity.kpis import REGISTRY


def main() -> None:
    print("--- 1. Confirm the install ---")
    print(f"mineproductivity {mineproductivity.__version__}")

    print()
    print("--- 2. A KPI is looked up by its governed identifier, not written by hand ---")
    tph_type = REGISTRY.get("PROD.TPH")
    tph = tph_type()
    print(f"resolved {tph_type.__name__} from the code 'PROD.TPH'")

    print()
    print("--- 3. Compute it: one CAT 793F's shift -- 40 haul cycles ---")
    # A 793F carries ~220 t per load and turns a cycle in ~18 min (0.3 h).
    # Forty cycles fills a 12 h shift: 8,800 t moved.
    cycles = [{"payload_t": 220.0, "operating_h": 0.3} for _ in range(40)]
    result = tph.compute(cycles)
    print(f"40 cycles x 220 t = {sum(c['payload_t'] for c in cycles):,.0f} t over 12.0 h")
    print(f"PROD.TPH = {result.value:.2f} {result.unit}")

    print()
    print("--- 4. The result carries provenance, not just a bare float ---")
    print(f"code    : {result.code}")
    print(f"unit    : {result.unit}")
    print(f"n       : {result.n} (rows that fed the computation)")
    print(f"warnings: {result.warnings}")

    print()
    print("--- 5. The Standard Library is discoverable ---")
    print(f"{len(REGISTRY)} KPIs are registered. The first five:")
    for code in sorted(REGISTRY)[:5]:
        print(f"  {code}")

    print()
    print("Nothing above hard-coded 'payload / hours'. The formula, its unit,")
    print("and its validity rules live inside the governed KPI object.")


if __name__ == "__main__":
    main()
