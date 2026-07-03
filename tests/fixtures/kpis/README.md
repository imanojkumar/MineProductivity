# KPI Engine Fixtures

## Purpose

A small, synthetic (not vendor-derived) one-shift sample dataset exercising every canonical event type the Standard Library's 12 flagship KPIs read, per design spec §30 (Certification Category A — golden datasets) and §31 (worked examples).

## Contents

All six files describe one shift, `A-2026-06-25` (`bingham-west`, 06:00–18:00 UTC):

- `cycle_events.csv` — 12 haul cycles across two trucks (`HT-214`, `HT-215`), a mix of ore and waste, each leg-time sum exactly one hour so `PROD.TPH`/`HAUL.TruckCycleTime`/`QUAL.OreProportion` all produce clean, hand-checkable numbers.
- `maintenance_events.csv` — one unplanned hour of downtime on `HT-215`, for `UTIL.PA`/`UTIL.UA`.
- `production_events.csv` — one shift-level production reading against plan, for `UTIL.UA`/`UTIL.Performance`.
- `consumption_events.csv` — fuel burn for both trucks, for `ENERGY.FuelConsumed`/`COST.FuelPerTonne`.
- `delay_events.csv` — two delays (`Equipment`, `Process` categories), for `DISP.TotalDelayHours`.
- `safety_events.csv` — two speed violations, for `SAFE.SpeedViolationCount`.

Every timestamp falls strictly inside `[06:00:00, 18:00:00)` UTC — `EventQuery.until_utc` is exclusive, so a row placed exactly at the shift boundary would be silently dropped from a shift-scoped query.

## Dependencies

Consumed by `examples/kpis/_dataset.py` (the example scripts' shared loader) and `tests/integration/test_kpi_pipeline.py`.

## References

- [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../../../docs/architecture/05_KPI_Engine_Design_Specification.md) §30, §31.
