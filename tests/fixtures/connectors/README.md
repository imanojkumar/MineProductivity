# Connector Framework Fixtures

## Purpose

Small, synthetic (not vendor-derived) CSV fixtures exercising `CSVConnector` -- and, transitively, `FileRowNormalizer`, `parse_source_datetime`, and the Event Framework pipeline downstream of it -- against known-shape data, per design spec §29 ("Recorded-fixture tests") and §30 (Certification Categories A/C/D/F).

## Contents

- `cycle_events.csv` / `delay_events.csv` — the golden fixture pair: well-formed rows only, used to prove exact `CycleEvent`/`DelayEvent` reproduction (Category A) and the full CSV → connector → `EventValidator` → `EventStore` → query pipeline (Category B). See `tests/integration/test_connector_pipeline.py`.
- `malformed_cycle_events.csv` — nine rows, two deliberately malformed (a non-numeric leg minute, a missing `payload_t`), proving one bad row never aborts ingestion of the rest (Category D).
- `local_timezone_cycle_events.csv` — two rows with local, non-UTC `event_time` values, proving correct normalization to UTC when `source_timezone` is set (Category F).

## Dependencies

`mineproductivity.connectors.CSVConnector`, consumed by `tests/unit/connectors/` and `tests/integration/test_connector_pipeline.py`.

## References

- [`docs/architecture/04_Connector_Framework_Design_Specification.md`](../../../docs/architecture/04_Connector_Framework_Design_Specification.md) §29, §30.
