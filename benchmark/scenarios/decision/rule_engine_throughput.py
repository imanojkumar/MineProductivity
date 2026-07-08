"""Benchmark scenario: ``decision.RuleEngine.evaluate()`` throughput at
representative policy/rule-count scale (Decision Intelligence
implementation checklist, Benchmarks).

Standalone by design -- the ``mineproductivity.benchmark`` harness
package is not yet implemented (see ``benchmark/README.md``), so this
scenario is a plain script, mirroring ``scripts/quality/perf_smoke.py``'s
own disclosed, harness-free posture. Results are recorded in
``benchmark/reports/decision/``.

Scale rationale: a production site runs dozens of policies, each
bundling a handful of rules; 10/50/250 rules per evaluation spans "one
policy" through "every policy a site owns, evaluated as one batch."
Half the rules trigger, half do not, and one rule always raises -- so
the measured path includes the isolation machinery, not just the happy
path.

Run: python benchmark/scenarios/decision/rule_engine_throughput.py
"""

from __future__ import annotations

import logging
import platform
import time

from mineproductivity.core import PredicateSpecification

from mineproductivity.decision import DecisionContext, Rule, RuleEngine
from mineproductivity.kpis import KPIResult

ITERATIONS_BY_RULE_COUNT = {10: 2_000, 50: 1_000, 250: 200}


def _context() -> DecisionContext:
    return DecisionContext(
        kpi_results=(
            KPIResult(code="UTIL.OEE", value=0.83, unit=""),
            KPIResult(code="PROD.TPH", value=207.1, unit="t/h"),
            KPIResult(code="MAINT.MTBF", value=118.0, unit="h"),
        ),
        analytics_results=(),
        scope={"pit": "north", "shift": "A-2026-06-25"},
    )


def _rules(count: int) -> dict[str, Rule]:
    rules: dict[str, Rule] = {}
    for index in range(count - 1):
        if index % 2 == 0:
            rules[f"rule_{index:04d}_triggers"] = PredicateSpecification(
                lambda ctx: any(r.value is not None and r.value < 1000.0 for r in ctx.kpi_results)
            )
        else:
            rules[f"rule_{index:04d}_quiet"] = PredicateSpecification(
                lambda ctx: any(r.value is not None and r.value < 0.0 for r in ctx.kpi_results)
            )
    # One deliberately malformed rule, so the isolation path is always
    # part of what is measured (design spec 07 sec. 10).
    rules["rule_malformed_raises"] = PredicateSpecification(
        lambda ctx: bool(ctx.kpi_results[999].value)
    )
    return rules


def main() -> None:
    # The malformed rule fires RuleEngine's per-failure warning on every
    # evaluation; measured here is the isolation machinery itself, not
    # the console I/O of 3,200 log lines -- so the logger is silenced
    # for the duration of the run.
    logging.getLogger("mineproductivity.decision.rules").setLevel(logging.ERROR)

    print("RuleEngine.evaluate() throughput")
    print(f"python={platform.python_version()} machine={platform.machine()}")
    print()
    print(f"{'rules':>6} {'iterations':>11} {'total_s':>9} {'eval/s':>10} {'rules/s':>12}")

    engine = RuleEngine()
    context = _context()
    for rule_count, iterations in ITERATIONS_BY_RULE_COUNT.items():
        rules = _rules(rule_count)
        # Warm-up (import costs, first-call caches) kept out of the
        # measured window.
        engine.evaluate(rules, context)
        start = time.perf_counter()
        for _ in range(iterations):
            engine.evaluate(rules, context)
        elapsed = time.perf_counter() - start
        evaluations_per_second = iterations / elapsed
        rules_per_second = (iterations * rule_count) / elapsed
        print(
            f"{rule_count:>6} {iterations:>11} {elapsed:>9.3f}"
            f" {evaluations_per_second:>10.0f} {rules_per_second:>12.0f}"
        )


if __name__ == "__main__":
    main()
