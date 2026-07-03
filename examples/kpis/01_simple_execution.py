"""Simple, single-KPI execution: ``PROD.TPH`` end-to-end, mirroring
design spec §31's worked example -- resolve the shift, scan the event
store, compute, and read the result back.

Run: python examples/kpis/01_simple_execution.py
"""

from __future__ import annotations

from _dataset import SHIFT_ID, build_engine


def main() -> None:
    engine = build_engine()

    print("--- 1. Execute a single KPI for a single shift ---")
    result = engine.execute("PROD.TPH", window="shift", scope={"shift": SHIFT_ID})
    assert result.is_ok
    tph = result.unwrap()
    print(f"PROD.TPH = {tph.value:.1f} {tph.unit} (from {tph.n} cycle events)")

    print()
    print("--- 2. KPIResult carries provenance, not just a bare number ---")
    print(f"code={tph.code!r} unit={tph.unit!r} n={tph.n} warnings={tph.warnings}")

    print()
    print("--- 3. A KPI with no matching data returns a warning-carrying result, never a crash ---")
    empty = engine.execute("PROD.TPH", window="shift", scope={"shift": "no-such-shift"})
    assert empty.is_ok
    empty_result = empty.unwrap()
    print(f"value={empty_result.value} warnings={empty_result.warnings}")

    print()
    print("--- 4. Export to a DataFrame via the active ExecutionBackend ---")
    frame = tph.to_frame()
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
