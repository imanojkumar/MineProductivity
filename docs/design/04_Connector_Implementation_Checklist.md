# Connector Framework — Implementation Checklist

**Package:** `mineproductivity.connectors`
**Governing specification:** [`docs/architecture/04_Connector_Framework_Design_Specification.md`](../architecture/04_Connector_Framework_Design_Specification.md)
**Status:** Not started

Binding implementation contract for `connectors`. Complete in order; every box must be checked or explicitly deferred with a linked issue and Chief Software Architect sign-off before merge.

## Pre-Implementation Gate

- [ ] Design specification read in full by the implementer.
- [ ] `core`, `ontology`, `events` available and importable; `io`, `config`, `registry` cross-cutting packages available.
- [ ] This checklist reviewed against the design spec's §36/§37 — no drift.
- [ ] Confirmed: no proprietary vendor SDK will be added as a dependency of this package (design spec §4, §34).

## Package Structure

- [ ] `src/mineproductivity/connectors/` created matching design spec §6: `base.py`, `normalization.py`, `auth.py`, `retry.py`, `health.py`, `file/`, `network/`, `streaming/`, `oem/`, `contract_tests.py`, `exceptions.py`, `__init__.py`, `README.md`.
- [ ] `connectors/README.md` written following the `core/README.md` template.
- [ ] Confirmed `oem/` modules contain shape-only classes (constructor signatures, no working vendor SDK calls).

## Public API

- [ ] `connectors/__init__.py` exports exactly the symbol list in design spec §8, alphabetized `__all__`.
- [ ] `test_public_api.py` mirrors `tests/unit/core/test_public_api.py`.

## Interfaces / Object Model

- [ ] `FMSConnector` ABC (§10.1) — `get_cycle_data`/`get_delay_data` abstract; `get_maintenance_data`/`get_production_data`/`get_consumption_data`/`get_safety_data`/`health_check` with no-op/default implementations.
- [ ] `Normalizer` ABC + `FieldMapper` + `ReasonCodeMap` (§10.2) — independently unit-testable without a live connection.
- [ ] `AuthProvider` ABC + `Credentials` (§10.3).
- [ ] `RetryPolicy` + `BackoffStrategy` (§10.3) — `FIXED`, `EXPONENTIAL`, `EXPONENTIAL_JITTER`.
- [ ] `ConnectorHealth` + `HealthStatus` (§10.4).
- [ ] `IngestionMode` enum (§10.5) — `BATCH`, `INCREMENTAL`, `STREAMING`.
- [ ] Reference connectors (§10.6): `CSVConnector`, `ExcelConnector`, `RestConnector`, `GraphQLConnector`, `KafkaConnector`, `MqttConnector`.
- [ ] OEM adapter shapes (§10.7): `MineStarConnector`, `DispatchConnector`, `WencoConnector`, `ModularConnector`, `HexagonConnector` — shape-only, documented as such in every docstring.

## Lifecycle & State Machine

- [ ] Connector lifecycle (§11): Instantiated → (Authenticated | Ready) → Pulling → (Ready | Retrying → Pulling/Failed) → Closed.
- [ ] `ConnectorHealth.status` state machine (§12): Unknown → Healthy ⇄ Degraded/Unhealthy, transitions updated after every pull attempt.

## Validation

- [ ] Shared contract test suite (`run_fms_contract_suite`, §9) implemented and exercised against `CSVConnector`.
- [ ] Contract suite asserts: well-formed events, `[since, until)` window respected, lazy `Iterable` returned (not a `list`), malformed records degrade per §26 rather than crash.

## Versioning

- [ ] Connector plugin SemVer discipline documented in `README.md`.
- [ ] `ReasonCodeMap` revision tracking confirmed independent of connector interface version.

## Serialization

- [ ] Confirmed connectors consume source-native formats and produce `events`-owned `BaseEvent` types — no new serialization format introduced by this package.
- [ ] `RetryPolicy`/`Credentials`/`ConnectorHealth` serialize via `core.serialization` for diagnostics.

## Performance & Memory

- [ ] Every `FMSConnector.get_*_data` implementation confirmed to be a generator (test: memory profile does not scale with a large synthetic fixture's row count).
- [ ] `RestConnector` reference implementation demonstrates paging with bounded per-request memory.
- [ ] Streaming connector backpressure behavior documented and tested against a bounded internal buffer.

## Thread Safety & Concurrency

- [ ] Each `FMSConnector` implementation documents its own thread-safety guarantee explicitly in its docstring.
- [ ] `AuthProvider.refresh()` confirmed safe under concurrent calls (no duplicate token acquisition, no `Credentials` corruption) — stress test required, this is a mandatory (not merely documented) guarantee per design spec §24.
- [ ] Multi-connector concurrent ingestion (e.g. CSV backfill + Kafka stream simultaneously) exercised in an integration test.

## Error Handling

- [ ] Full exception hierarchy (§26): `ConnectorError`, `MappingError`, `AuthenticationError`, `SourceUnavailableError`, `ContractViolationError`.
- [ ] Confirmed a single `MappingError` on one record does not abort the enclosing generator (dedicated test: N-1 good records + 1 bad record yields N-1 events + 1 logged error).

## Logging

- [ ] Unmapped vendor reason codes logged at `WARNING` with vendor name + raw code.
- [ ] Retry attempts logged at `INFO`; exhausted retries logged at `ERROR`.
- [ ] `ConnectorHealth` transitions into `Degraded`/`Unhealthy` logged at `WARNING`; recovery to `Healthy` logged at `INFO`.

## Configuration

- [ ] Per-connector configuration shapes (`CSVConnectorConfig`, `RestConnectorConfig`, etc.) implemented as `core.BaseConfiguration` subclasses.
- [ ] Confirmed `connectors` reads no environment variables or files directly.

## Tests

- [ ] `tests/unit/connectors/` mirrors `src/mineproductivity/connectors/` 1:1.
- [ ] Coverage ≥95%.
- [ ] Recorded, anonymized fixtures committed under `tests/fixtures/connectors/` for each reference source type.
- [ ] Retry/backoff tests use an injected fake clock — no real sleeping in the unit test suite.
- [ ] Semantic-recomputation rule (design spec §13.3) covered by a dedicated fixture scenario with a deliberately mismatched vendor denominator.

## Documentation

- [ ] `connectors/README.md` complete.
- [ ] Every OEM shape class's docstring explicitly states it is documentation-only, non-functional.

## Examples

- [ ] `examples/connectors/01_csv_ingestion.py` — end-to-end CSV → events, mirrors design spec §31.
- [ ] `examples/connectors/02_rest_with_retry.py` — mocked HTTP server demonstrating auth-refresh and retry/backoff.
- [ ] All examples pass `mypy --strict` + `ruff`.

## Benchmarks

- [ ] Large-fixture (synthetic, CI-scaled) CSV ingestion throughput recorded in `benchmark/reports/connectors/`.
- [ ] Retry/backoff timing behavior recorded for the documented `BackoffStrategy` variants.

## Certification

- [ ] Categories A (golden), B (integration), C (edge cases), D (corrupted data), F (timezone) from design spec §30 pass against `CSVConnector`.
- [ ] Contract suite conformance proof (design spec §37.1) demonstrated for `CSVConnector` and `RestConnector`.

## Type Hints, Mypy, Ruff, Coverage

- [ ] 100% type-hinted; `mypy --strict` clean.
- [ ] `ruff check` and `ruff format --check` clean.
- [ ] Coverage report attached; ≥95%.

## Release

- [ ] `CHANGELOG.md` updated.
- [ ] Root README dependency diagram cross-checked — confirm no forbidden import (`kpis`, `analytics`, etc.) was introduced (mechanical AST-based check, mirroring `core`'s pattern).
- [ ] Version bump proposed and reviewed.
- [ ] Design spec §37 re-verified as final merge gate.

---

*Derived from [`04_Connector_Framework_Design_Specification.md`](../architecture/04_Connector_Framework_Design_Specification.md). Keep in sync with the governing specification.*
