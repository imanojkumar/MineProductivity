# mineproductivity.connectors

## Purpose

`mineproductivity.connectors` is how MineProductivity meets the real world. It defines the single, small contract every data source — a fleet-management system, a CSV export, a REST API, a Kafka topic — must satisfy to feed the platform, and it is the **only** place in the codebase permitted to know that a specific vendor or file format exists (the Cookbook's Vendor-Neutrality principle: "Connectors are the only place in the codebase allowed to know about a specific OEM").

This package implements the [Connector Framework Design Specification](../../../docs/architecture/04_Connector_Framework_Design_Specification.md) exactly. Where this README and that specification disagree, the specification governs.

## Scope

**What belongs here:**

- The `FMSConnector` abstract contract and `IngestionMode`.
- `Normalizer`/`FieldMapper`/`ReasonCodeMap` — the vendor-dialect-to-canonical translation layer, independently unit-testable without a live connection.
- `AuthProvider`/`Credentials`, `RetryPolicy`/`BackoffStrategy` — shared, generic network-connector plumbing.
- `ConnectorHealth`/`HealthStatus`.
- Reference connectors: `CSVConnector`, `ExcelConnector` (file), `RestConnector`, `GraphQLConnector` (network), `KafkaConnector`, `MqttConnector` (streaming).
- OEM adapter **shapes** for MineStar, DISPATCH, Wenco, Modular Mining, and Hexagon — mapping/constructor contracts only, never working vendor integrations.
- `run_fms_contract_suite` — the shared structural contract every connector, built-in or plugin, is expected to pass.

**What must never belong here:**

- Event definitions (`CycleEvent`, `DelayEvent`, ...) — owned by `events`; connectors *produce* instances of these types, never redefine their shape.
- Ontology entity definitions — owned by `ontology`; connectors *resolve against* entities, never define them.
- KPI computation — connectors never import `kpis`.
- Actual vendor SDK code or credentials. This repository never bundles a proprietary OEM SDK; a real MineStar/DISPATCH/Wenco/Hexagon connector is an independent plugin package with its own dependency on the vendor's SDK, isolated entirely from this package's own dependency graph.
- A specific broker client library (`kafka-python`, `paho-mqtt`, ...) — see `KafkaConnector`/`MqttConnector`'s Design Rationale entry below.

## Architecture

```
core → ontology → events → connectors
                              ↑
                    (also) registry
```

`connectors` sits after `events` and `ontology` in the dependency stack — it produces events and resolves ontology reference data, but is itself a plumbing package (Cookbook Part I, Ch. 3's three-band model: "domain heart," "plumbing," "intelligence/interfaces").

Everything left of the `Normalizer` boundary in the data flow below may know about a vendor's dialect. Nothing right of it ever does — this single boundary is the entire value of the Connector Framework:

```
Source (file / vendor SDK / REST / Kafka / MQTT)
   |
   v
FMSConnector.get_cycle_data() / get_delay_data() / ...   (streamed, one record at a time)
   |
   v
Normalizer.normalize_cycle() / .normalize_delay()
   |  FieldMapper: vendor field names -> canonical field names
   |  ReasonCodeMap: vendor reason codes -> canonical DelayCategory (ontology)
   v
canonical BaseEvent instance (events package's types)
```

Only `get_cycle_data` and `get_delay_data` are abstract on `FMSConnector` (design spec AD-CN-01); the remaining four `get_*_data` methods have no-op defaults, so a CSV-only source is never forced to stub out methods it has nothing to yield for. Every `get_*_data` implementation is a lazy generator — memory footprint is independent of source size, mechanically checked by `run_fms_contract_suite`.

See the [design specification's §10](../../../docs/architecture/04_Connector_Framework_Design_Specification.md) for the full object model, lifecycle, and sequence diagrams.

## Package Structure

```
connectors/
├── __init__.py            # public API surface (__all__); registers the 6 built-in connectors
├── _registry.py             # CONNECTORS, get_connector, register_connector (internal, avoids a circular import)
├── base.py                    # FMSConnector, IngestionMode
├── normalization.py             # Normalizer, FieldMapper, ReasonCodeMap
├── auth.py                        # AuthProvider, Credentials, _StaticAuthProvider (reference)
├── retry.py                         # RetryPolicy, BackoffStrategy, run_with_retry
├── health.py                          # ConnectorHealth, HealthStatus
├── contract_tests.py                    # run_fms_contract_suite
├── exceptions.py                          # the connectors exception hierarchy
├── file/                                    # File-based reference connectors
│   ├── _common.py                             # FileRowNormalizer, parse_source_datetime (shared)
│   ├── csv_connector.py                         # CSVConnector
│   └── excel_connector.py                        # ExcelConnector (optional openpyxl dependency)
├── network/                                 # Network-based reference connectors
│   ├── rest_connector.py                      # RestConnector (stdlib urllib only)
│   └── graphql_connector.py                     # GraphQLConnector (stdlib urllib only)
├── streaming/                               # Streaming reference connectors
│   ├── _common.py                             # consume_message_source (shared)
│   ├── kafka_connector.py                       # KafkaConnector
│   └── mqtt_connector.py                          # MqttConnector
├── oem/                                     # OEM adapter SHAPES (no vendor SDK code)
│   ├── minestar_shape.py, dispatch_shape.py, wenco_shape.py, modular_shape.py, hexagon_shape.py
└── README.md                                # this file
```

## Dependency Rules

```
core → ontology → events → connectors
                              ↑
                    (also) registry
```

- **`connectors` depends on:** `core`, `ontology`, `events`, and `registry`.
- **`connectors` is depended on by:** nothing in the domain-heart or intelligence layers directly — the platform depends on `connectors` only through the `events` it produces, never through a direct import.
- **Forbidden (the single most load-bearing rule in this document):** `connectors` MUST NOT import `kpis`, `analytics`, `optimization`, `simulation`, `decision`, `digital_twin`, or `agents`. This is mechanically checked by `tests/unit/connectors/test_public_api.py::TestNoForbiddenDependencies`.

## Public API

```python
from mineproductivity.connectors import (
    FMSConnector, get_connector, register_connector, CONNECTORS,
    Normalizer, FieldMapper, ReasonCodeMap,
    AuthProvider, Credentials, RetryPolicy, BackoffStrategy,
    ConnectorHealth, HealthStatus,
    CSVConnector, ExcelConnector, RestConnector, GraphQLConnector,
    KafkaConnector, MqttConnector,
    IngestionMode,
    ConnectorError, MappingError, AuthenticationError,
    SourceUnavailableError, ContractViolationError,
)
```

`CSVConnector`, `ExcelConnector`, `RestConnector`, `GraphQLConnector`, `KafkaConnector`, and `MqttConnector` are registered into `CONNECTORS` automatically at import time (`"csv" in CONNECTORS` is `True` with no setup). OEM shape classes (`MineStarConnector`, ...) are deliberately **not** part of this top-level surface or auto-registered — import them from `mineproductivity.connectors.oem` directly. `run_fms_contract_suite` is accessed via `mineproductivity.connectors.contract_tests.run_fms_contract_suite` (design spec §9 — an internal-API-documented, not top-level-exported, symbol).

## Extension Guide

**Adding a new connector.** Implement `FMSConnector`, declare a unique `name`, and decorate with `@register_connector`:

```python
from mineproductivity.connectors import FMSConnector, register_connector

@register_connector
class WencoConnector(FMSConnector):
    name = "wenco"
    ...
```

```toml
# In a THIRD-PARTY plugin package's pyproject.toml
[project.entry-points."mineproductivity.connectors"]
wenco = "mineproductivity_wenco.connector:WencoConnector"
```

After `pip install mineproductivity-wenco`, `get_connector("wenco")` works with zero core change (Cookbook Part I, Ch. 7).

**Adding a new `ReasonCodeMap`.** Build one independently of any connector or live source — it is a pure, frozen value object:

```python
from mineproductivity.connectors import ReasonCodeMap
from mineproductivity.ontology import DelayCategory

my_vendor_map = ReasonCodeMap(
    vendor_name="my_vendor",
    mapping={"EQ_DOWN": (DelayCategory.EQUIPMENT, "equipment down")},
)
```

**Running the shared contract suite against a new connector:**

```python
from mineproductivity.connectors.contract_tests import run_fms_contract_suite

run_fms_contract_suite(
    lambda: MyConnector(...),
    since=since, until=until,
    expected_cycle_count=3,  # fixture-dependent
)
```

## Examples

Runnable, narrated scripts live in [`examples/connectors/`](../../../examples/connectors/README.md):

| Script | Demonstrates |
|---|---|
| `01_csv_ingestion.py` | `get_connector("csv")` → pull → validate → envelope → append → query, end to end. |
| `02_rest_with_retry.py` | `RestConnector` against a real local HTTP server: a 401-triggered auth refresh and a retried transient 503. |

## Design Rationale

- **Why does `FMSConnector` have only two abstract methods?** Matches the Cookbook's minimal contract exactly and keeps the barrier to writing a first connector as low as possible (design spec AD-CN-01) — a CSV-only source is never forced to stub out methods it has nothing to yield for.
- **Why are `Normalizer`/`FieldMapper`/`ReasonCodeMap` separate, independently testable objects instead of private methods inside each `FMSConnector` subclass?** Composition over inheritance (AD-CN-02); a vendor's mapping table can be reviewed, versioned, and unit-tested by a domain expert who never has to read or run the connector's I/O code.
- **Why do OEM adapter classes exist in this package only as documentation-only shapes?** Keeps this package's own dependency graph free of any proprietary vendor SDK, preserving pip-installability and open-source distributability of the core package (AD-CN-03).
- **Why do `KafkaConnector`/`MqttConnector` take a plain `Iterable[Mapping[str, Any]]` message source instead of depending on `kafka-python`/`paho-mqtt`?** The same reasoning as AD-CN-03, extended to broker client libraries: this package stays installable and testable without a running Kafka/MQTT broker or a heavy client dependency. A real `mineproductivity-kafka`/`mineproductivity-mqtt` plugin wraps the vendor client to produce the same shape. Because the connector only pulls the next message when its own caller asks for the next event, no unbounded buffering happens inside the connector — backpressure (design spec §22) is inherent to the lazy-generator chain, not a separate mechanism to implement.
- **Why do `RestConnector`/`GraphQLConnector` use the standard library's `urllib` instead of a third-party HTTP client?** Consistent with the base install's "essential packaging requirements only" promise (mirroring `events.EventID`'s stdlib-only ULID implementation) — no `requests`/`httpx` dependency is required just to `import mineproductivity.connectors`.
- **Why does `CSVConnector` take two file paths (`path`, `delay_path`) instead of one?** A real FMS export typically ships cycles and delays as separate homogeneous-schema files rather than interleaved rows of different shapes; `delay_path` is optional since some sources (a cycle-only export) have no delay data. `ExcelConnector` mirrors the same shape for `.xlsx` workbooks.
- **Why is `openpyxl` an optional dependency (the `connectors` extra) rather than a base requirement?** The same "pay only for what you use" principle as `events`' optional `pyarrow` dependency for `ArrowEventCodec`/`ParquetEventCodec` — importing `mineproductivity.connectors` never requires `openpyxl` unless an `ExcelConnector` is actually instantiated and read from (the import happens lazily inside `_iter_rows`, never at module load time).
- **Why does the `connectors` extra also pull in `tzdata` on Windows?** Python's `zoneinfo` module relies on the operating system's IANA time zone database, which Windows does not ship; `tzdata` is the official PyPI companion package `zoneinfo` itself recommends for platforms without one. Scoped to `sys_platform == 'win32'` so Linux/macOS installs, which already have the OS database, pull in nothing extra.

## Anti-Patterns

- ❌ **Any code outside `connectors` importing a vendor SDK.** If `kpis` or `events` ever needs to `import minestar_sdk`, the architecture has already failed — the whole point of this package is that this never happens.
- ❌ **A connector returning a `list` instead of yielding.** Fails the contract suite immediately and defeats the "200-row test file or 50-million-row export, same code" guarantee.
- ❌ **Copying a vendor's pre-computed availability/utilisation percentage** instead of recomputing from time buckets when denominators differ (design spec §13.3, normative-severity per the Developer & Cookbook Guide Part III).
- ❌ **Letting one malformed record abort an entire ingestion run.** Log and skip (`MappingError` per record, never per batch) — a whole shift's data must not be lost because one row has a typo.
- ❌ **Hard-coding a vendor's reason codes as `if/elif` chains inside connector logic** instead of an externally-maintainable `ReasonCodeMap`.
- ❌ **A connector plugin skipping the shared contract test suite** "because our vendor is different." Every connector, however exotic its source, satisfies the same small contract.
- ❌ **Catching `Exception` instead of `ConnectorError`/`MineProductivityError`** when handling a connector failure. Every exception this package raises derives from `core.MineProductivityError` specifically so callers do not need a broad `except Exception`.

## Testing & Quality

- `tests/unit/connectors/` — one `test_*.py` per source module (mirroring `file/`, `network/`, `streaming/`, `oem/` as subpackages too) — **100% line coverage**.
- `tests/fixtures/connectors/` — small, synthetic CSV fixtures (golden, malformed, local-timezone variants) exercising `CSVConnector` against known-shape data.
- `tests/integration/test_connector_pipeline.py` — the full CSV → `CSVConnector` → `EventValidator` → `EventStore` → query pipeline, plus Certification Categories A (golden), C (edge cases), D (corrupted data), and F (timezone).
- `RestConnector`/`GraphQLConnector` are tested against a real, local `http.server.HTTPServer` — genuine socket I/O, not a patched client.
- `mypy --strict` and `ruff` are clean on `src/mineproductivity/connectors/`, `tests/unit/connectors/`, `tests/integration/test_connector_pipeline.py`, and `examples/connectors/`.

## Contents

See [Package Structure](#package-structure) above for the full file layout.

## Dependencies

**Depends on:** `core`, `ontology`, `events`, `registry`. Optionally, `openpyxl` and (on Windows) `tzdata` (the `connectors` extra) for `ExcelConnector` and correct local-timezone normalization — imported lazily, never required to `import mineproductivity.connectors`.

**Depended on by:** nothing directly; the platform consumes `connectors` only through the `events` it produces.

## Future Work

- Database/historian connectors (Cookbook Part I, Ch. 7: "Query a historian or SQL table in pages") — the same `FMSConnector` shape, a new `network/` or `database/` module.
- Bidirectional connectors for future dispatch/optimization write-back — out of scope for the read-only ingestion focus of this milestone.
- Real `mineproductivity-kafka`/`mineproductivity-mqtt` plugin packages wrapping actual broker client libraries to the `Iterable[Mapping[str, Any]]` shape `KafkaConnector`/`MqttConnector` already expect.

## References

- Master Architecture Handbook v1.0
- Reference Implementation Blueprint v1.0
- [`docs/architecture/04_Connector_Framework_Design_Specification.md`](../../../docs/architecture/04_Connector_Framework_Design_Specification.md)
- [`docs/design/04_Connector_Implementation_Checklist.md`](../../../docs/design/04_Connector_Implementation_Checklist.md)
- Developer & Cookbook Guide Part I, Chapter 5 ("Your First Event") and Chapter 7 ("Connectors: Meeting the Real World")
- Developer & Cookbook Guide Part III, "Compatibility with external systems" (the semantic-recomputation rule)
