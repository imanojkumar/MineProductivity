# Examples - mineproductivity.kpis

## Purpose

Runnable, minimal, self-contained scripts demonstrating the KPI Engine: single-KPI execution, composite dependency resolution, batched multi-KPI scans, and registry discovery, all against one realistic, one-shift sample dataset.

## Scope

Example scripts and their direct output. No test assertions live here (see `tests/unit/kpis/` and `tests/integration/test_kpi_pipeline.py` for that); each script is meant to be read and run by a human evaluating the package.

## Responsibilities

- Show idiomatic usage of the KPI Engine's public API.
- Serve as executable documentation that stays correct because it is actually run.

## Contents

- `_dataset.py` - shared, internal loader: parses the sample dataset in `tests/fixtures/kpis/` into canonical events, appends them to an in-memory `EventStore`, and builds a real `KPIEngine` wired to the full Standard Library `REGISTRY`. Not itself an example; every script below imports it.
- `01_simple_execution.py` - `PROD.TPH` end-to-end (design spec §31): resolve the shift, scan the event store, compute, read the result's provenance, export to a DataFrame.
- `02_composite_oee.py` - `UTIL.OEE` composite execution: the engine resolves `UTIL.PA` / `UTIL.UA` / `UTIL.Performance` first, then combines them; also shows `None` propagating through the composite when a dependency has no data.
- `03_batch_summary.py` - `KPIEngine.summary()` computing nine KPIs across every category in a single call, sharing one event-store scan across KPIs that read the same event types.
- `04_discovery.py` - `REGISTRY` introspection: listing every registered code, filtering by namespace and by composite-vs-leaf, and fully describing a KPI's governed metadata without reading its source.

## Sample Dataset

`tests/fixtures/kpis/` holds one realistic shift (`A-2026-06-25`, 06:00–18:00 UTC, `bingham-west`) as six CSV files — `cycle_events.csv`, `maintenance_events.csv`, `production_events.csv`, `consumption_events.csv`, `delay_events.csv`, `safety_events.csv` — covering every canonical event type the Standard Library's 12 flagship KPIs read. See `tests/fixtures/kpis/README.md` for the full schema.

## Dependencies

`mineproductivity[analytics]` (for the `pandas`-backed default `ExecutionBackend`). No network access; the sample dataset is local.

## Running the Examples

```bash
pip install -e ".[analytics]"
python examples/kpis/01_simple_execution.py
python examples/kpis/02_composite_oee.py
python examples/kpis/03_batch_summary.py
python examples/kpis/04_discovery.py
```

Each script exits `0` and prints its own output; there is nothing to configure.

## Future Work

Add a backend-selection walkthrough (`set_active_backend`) once a representative fleet-scale dataset exists to make the Polars/DuckDB/NumPy performance difference visible rather than academic.

## References

- Developer & Cookbook Guide Part III, KPI Standard Library
- [`docs/architecture/05_KPI_Engine_Design_Specification.md`](../../docs/architecture/05_KPI_Engine_Design_Specification.md) §31
- [`src/mineproductivity/kpis/README.md`](../../src/mineproductivity/kpis/README.md)
