# Examples — mineproductivity.decision

## Purpose

Runnable, minimal, self-contained scripts demonstrating Decision Intelligence: an audited, explained, ranked decision pipeline over real KPI/Analytics evidence, action prioritization and dependency-respecting planning, live event-driven decision sessions, and third-party strategy plugins.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/decision/` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the Decision Intelligence public API.
- Serve as executable documentation that stays correct because it is actually run.
- Demonstrate the §3.2 discipline end-to-end: every fact a `DecisionPipeline` reasons over comes from `kpis.KPIEngine.execute()` or `analytics.BatchAnalyticsRunner` — nothing in `decision` recomputes a KPI or a statistic.

## Contents

- `_evidence.py` — shared, internal helper: parses the cycle/maintenance/production CSVs from the `tests/fixtures/kpis/` sample dataset (the same one `examples/kpis/` uses), builds a real `KPIEngine`, and carries five prior shifts' already-computed `UTIL.OEE` values for trend context. Not itself an example; the evidence-driven scripts below import it.
- `01_pipeline_over_evidence.py` — the design spec §9 worked example, end-to-end: a fleet-availability `Policy` evaluated against the real shift's `UTIL.OEE` and its week-long `TREND.Linear` slope — rule evaluation (`RuleEngineStage`), recommendation (`ThresholdDecisionStrategy`), declarative `Threshold` confirmation, explanation (`ExplanationStage`), ranking (`WeightedScoreRanking`), and the `DecisionAuditTrail` record, all through `DecisionPipeline`/`BatchDecisionRunner`.
- `02_action_planning.py` — `ActionPrioritizer` + `ActionPlanner`: ranking ("which recommendation is best," §16) kept distinct from prioritization ("which action happens first under limited capacity," §20), a dependency-respecting `ActionPlan` (§21), and the loud `Result.err` rejection of a cyclic dependency declaration.
- `03_realtime_session.py` — `RealTimeDecisionSession` over an `events.EventBus`: each published cycle event refreshes that equipment's `PROD.TPH` through the real `KPIEngine` and re-runs the pipeline; `latest()` serves per-scope results without re-running; includes a real-time/batch parity check and per-event audit-trail traceability.
- `04_plugin_strategy.py` — a third-party-style `DecisionStrategy` registered via entry points (`EntryPointSpec(group="mineproductivity.decision", target_registry="decision")`, design spec §32), mirroring `examples/registry/01_register_and_discover.py`'s real-discovery pattern.

## Sample Dataset

`tests/fixtures/kpis/` holds one realistic shift (`A-2026-06-25`, 06:00–18:00 UTC, `bingham-west`); `_evidence.py` loads the three event types `UTIL.OEE`'s dependency graph consumes. The five prior shifts' OEE values in `_evidence.OEE_HISTORY` are disclosed stand-ins for results a production deployment would read back from its own KPI store — the fixture dataset covers a single shift, so earlier points cannot be recomputed here.

## Dependencies

`mineproductivity[analytics]` (for the `pandas`-backed default `ExecutionBackend`). No network access; the sample dataset is local.

## Running the Examples

```bash
pip install -e ".[analytics]"
python examples/decision/01_pipeline_over_evidence.py
python examples/decision/02_action_planning.py
python examples/decision/03_realtime_session.py
python examples/decision/04_plugin_strategy.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a concrete `RootCauseAnalyzer`/`WhatIfEngine` walkthrough once a first-party or third-party plugin implementing either interface-only extension point exists (deliberately never shipped inside `decision` itself, design spec §33).

## References

- [`docs/architecture/07_Decision_Intelligence_Design_Specification.md`](../../docs/architecture/07_Decision_Intelligence_Design_Specification.md) §9, §16, §20–§21, §25–§27, §32
- [`src/mineproductivity/decision/README.md`](../../src/mineproductivity/decision/README.md)
- [`docs/adr/ADR-0007-Decision-Intelligence.md`](../../docs/adr/ADR-0007-Decision-Intelligence.md)
