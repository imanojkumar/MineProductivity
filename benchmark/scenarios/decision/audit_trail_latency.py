"""Benchmark scenario: ``decision.DecisionAuditTrail`` append/query
latency at representative audit-trail sizes (Decision Intelligence
implementation checklist, Benchmarks).

Standalone by design -- the ``mineproductivity.benchmark`` harness
package is not yet implemented (see ``benchmark/README.md``), so this
scenario is a plain script, mirroring ``scripts/quality/perf_smoke.py``'s
own disclosed, harness-free posture. Results are recorded in
``benchmark/reports/decision/``.

Scale rationale: one decision per equipment per shift across a large
fleet accumulates ~10^4 entries per month per site; 10^3/10^4/10^5
spans "a busy week" through "a year, never pruned." ``record()`` per-
entry cost must stay flat across sizes (the O(1)-append proof);
``query()``'s linear scan is a disclosed reference-implementation
posture (see ``audit.py``'s own performance note), measured here so the
trade-off is a recorded number, not a guess.

Run: python benchmark/scenarios/decision/audit_trail_latency.py
"""

from __future__ import annotations

import platform
import time
from datetime import datetime, timezone

from mineproductivity.decision import DecisionAuditEntry, DecisionAuditTrail, DecisionResult

TRAIL_SIZES = (1_000, 10_000, 100_000)
QUERY_REPEATS = 20


def _entry(index: int) -> DecisionAuditEntry:
    return DecisionAuditEntry(
        recorded_at=datetime(2026, 7, 8, tzinfo=timezone.utc),
        result=DecisionResult(model_code="STRATEGY.Threshold"),
        context_scope={"pit": "north" if index % 2 == 0 else "south", "shift": "A"},
        source_event_ids=(),
    )


def main() -> None:
    print("DecisionAuditTrail append/query latency")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(
        f"{'entries':>8} {'append_us':>10} {'query_all_ms':>13}"
        f" {'query_scope_ms':>15} {'matches':>8}"
    )

    for size in TRAIL_SIZES:
        trail = DecisionAuditTrail()
        entries = [_entry(index) for index in range(size)]

        start = time.perf_counter()
        for entry in entries:
            trail.record(entry)
        append_seconds = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(QUERY_REPEATS):
            unfiltered = trail.query()
        query_all_seconds = (time.perf_counter() - start) / QUERY_REPEATS

        start = time.perf_counter()
        for _ in range(QUERY_REPEATS):
            filtered = trail.query(scope={"pit": "north"})
        query_scope_seconds = (time.perf_counter() - start) / QUERY_REPEATS

        assert len(unfiltered) == size
        print(
            f"{size:>8} {append_seconds / size * 1e6:>10.2f}"
            f" {query_all_seconds * 1e3:>13.2f}"
            f" {query_scope_seconds * 1e3:>15.2f} {len(filtered):>8}"
        )


if __name__ == "__main__":
    main()
