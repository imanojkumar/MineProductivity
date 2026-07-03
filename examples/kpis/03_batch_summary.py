"""Batched multi-KPI execution: ``KPIEngine.summary()`` scans the event
store once per distinct ``required_events`` set shared across the
requested KPIs (and their transitive dependencies), not once per KPI
(design spec §22) -- the ``mine.summary(...)`` equivalent.

Run: python examples/kpis/03_batch_summary.py
"""

from __future__ import annotations

from _dataset import SHIFT_ID, build_engine

from mineproductivity.kpis import REGISTRY


def main() -> None:
    engine = build_engine()

    codes = [
        "PROD.TPH",
        "UTIL.OEE",
        "HAUL.TruckCycleTime",
        "MAINT.MTTR",
        "DISP.TotalDelayHours",
        "ENERGY.FuelConsumed",
        "COST.FuelPerTonne",
        "QUAL.OreProportion",
        "SAFE.SpeedViolationCount",
    ]

    print(f"--- Requesting {len(codes)} KPIs in a single summary() call ---")
    result = engine.summary(codes, window="shift", scope={"shift": SHIFT_ID})
    assert result.is_ok
    summary = result.unwrap()

    print()
    header = f"{'KPI':<24}{'Value':>12}  {'Unit':<8}{'n':>5}"
    print(header)
    print("-" * len(header))
    for code in codes:
        kpi_result = summary[code]
        value = f"{kpi_result.value:.3f}" if kpi_result.value is not None else "None"
        print(f"{code:<24}{value:>12}  {kpi_result.unit:<8}{kpi_result.n:>5}")

    print()
    print("--- Rows backing PROD.TPH and HAUL.TruckCycleTime were fetched exactly once, ---")
    print("--- shared between them since both read only the CYCLE event stream. ---")
    tph_cls = REGISTRY.get("PROD.TPH")
    tph_rows, tph_fingerprint = engine.rows_for(tph_cls(), "shift", {"shift": SHIFT_ID})
    print(
        f"PROD.TPH matched {tph_fingerprint} CYCLE envelopes, {len(tph_rows)} rows after assembly"
    )


if __name__ == "__main__":
    main()
